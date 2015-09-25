import datetime

import celery.beat
import mock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from celerycontrib.sqlalchemyscheduler import model, SQLAlchemyScheduler

DATABASE_URL = 'sqlite://'


@pytest.yield_fixture
def example_database():
    url = DATABASE_URL
    engine = create_engine(url)
    model.Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
    session = Session()
    objects = [
        model.PeriodicTask(
            name='example1',
            task='example1',
            interval_schedules=[model.IntervalSchedule(
                every=1,
                period='minutes',
            )],
            args='[1]',
        ),
        model.PeriodicTask(
            name='example2',
            task='example2',
            interval_schedules=[model.IntervalSchedule(
                every=1,
                period='minutes',
            )],
            args='[1]',
            enabled=False,
        ),
    ]
    session.add_all(objects)
    session.commit()
    yield session
    session.close()


@pytest.fixture
def scheduler(example_database):
    class Scheduler(SQLAlchemyScheduler):
        session = example_database
    return Scheduler(mock.MagicMock())


def test_load_entries(scheduler):

    scheduler.load_entries()

    entry = celery.beat.ScheduleEntry(
        app=scheduler.app,
        name='example1',
        task='example1',
        schedule=datetime.timedelta(minutes=1),
        args=[1],
        options=dict(
            expires=None,
            exchange=None,
            routing_key=None,
            queue=None,
        ),
    )

    assert list(scheduler.schedule.keys()) == ['example1']
    assert vars(scheduler.schedule['example1']) == vars(entry)
