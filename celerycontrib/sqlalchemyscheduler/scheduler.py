import json

import celery.beat
import sqlalchemy as sqla
from sqlalchemy import orm

from . import model


class SQLAlchemyScheduler(celery.beat.Scheduler):

    database_url = 'sqlite:///data.sqlite'

    _session = None

    @property
    def session(self):
        if self._session is None:
            engine = sqla.create_engine(self.database_url)
            Session = orm.sessionmaker(bind=engine)
            self._session = Session()
        return self._session

    def get_periodic_tasks(self):
        for periodic_task in self.session.query(model.PeriodicTask):
            yield periodic_task.name, dict(
                task=periodic_task.task,
                schedule=periodic_task.schedule,
                args=json.loads(periodic_task.args or 'null'),
                kwargs=json.loads(periodic_task.kwargs or 'null'),
                options=dict(
                    queue=periodic_task.queue,
                    exchange=periodic_task.exchange,
                    routing_key=periodic_task.routing_key,
                    expires=periodic_task.expires,
                ),
                last_run_at=periodic_task.last_run_at,
                total_run_count=periodic_task.total_run_count,
            )

    def setup_schedule(self):
        super(SQLAlchemyScheduler, self).setup_schedule()
        self.merge_inplace(dict(self.get_periodic_tasks()))

    def sync(self):
        super(SQLAlchemyScheduler, self).sync()
        for name, entry in self.schedule.items():
            task = self.session.query(model.PeriodicTask).filter(
                model.PeriodicTask.name == name
            ).first()
            if task is not None:
                task.last_run_at = entry.last_run_at
                task.total_run_count = entry.total_run_count
        self.session.commit()

    def close(self):
        super(SQLAlchemyScheduler, self).close()
        if self._session is not None:
            self.logger.debug('Closing database connection')
            self.session.close()
