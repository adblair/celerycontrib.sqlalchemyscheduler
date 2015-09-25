import json

import celery.beat
import sqlalchemy as sqla
from sqlalchemy import orm

from . import model


class SQLAlchemyScheduler(celery.beat.Scheduler):

    database_url = 'sqlite:///celerybeat-schedule.sqlite'

    _session = None
    _tasks_last_modified = None

    @property
    def session(self):
        if self._session is None:
            engine = sqla.create_engine(self.database_url)
            Session = orm.sessionmaker(bind=engine)
            self._session = Session()
        return self._session

    def generate_entry_dicts(self):
        query = self.session.query(model.PeriodicTask).filter(
            model.PeriodicTask.enabled)
        for periodic_task in query:
            for schedule in periodic_task.schedules:
                yield periodic_task.name, dict(
                    task=periodic_task.task,
                    schedule=schedule.schedule,
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

    def load_entries(self):
        self.merge_inplace(dict(self.generate_entry_dicts()))

    def save_entries(self):
        for name, entry in self.schedule.items():
            task = self.session.query(model.PeriodicTask).filter(
                model.PeriodicTask.name == name
            ).first()
            if task is not None:
                # TODO: Don't let this affect date_changed, somehow
                task.last_run_at = entry.last_run_at
                task.total_run_count = entry.total_run_count
        self.session.commit()

    def setup_schedule(self):
        super(SQLAlchemyScheduler, self).setup_schedule()
        self.sync()

    def sync(self):
        super(SQLAlchemyScheduler, self).sync()
        self.save_entries()
        self.load_entries()

    def get_tasks_last_modified(self):
        return self.session.query(
            sqla.func.max(model.PeriodicTask.date_changed)
        ).scalar()

    def should_sync(self):
        if super(SQLAlchemyScheduler, self).should_sync():
            return True
        else:
            self.logger.debug('Checking if database sync needed')
            tasks_last_modified = self.get_tasks_last_modified()
            if self._tasks_last_modified is None:
                should = True
            else:
                should = (tasks_last_modified > self._tasks_last_modified)
            self._tasks_last_modified = tasks_last_modified
            return should

    def close(self):
        super(SQLAlchemyScheduler, self).close()
        if self._session is not None:
            self.logger.debug('Closing database connection')
            self.session.close()
