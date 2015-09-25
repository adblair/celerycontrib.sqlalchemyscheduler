
from celery import Celery
from celerycontrib.sqlalchemyscheduler import (
    Base,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SQLAlchemyScheduler,
)
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.fields import Select2Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from wtforms.validators import ValidationError

BROKER_URL = 'amqp://guest@localhost//'
DATABASE_URL = 'sqlite:///example.sqlite'
SECRET_KEY = '0123456789'

flask = Flask(__name__)
celery = Celery(__name__, broker=BROKER_URL)
session = sessionmaker(bind=create_engine(DATABASE_URL))()

flask.config.update(
    SECRET_KEY=SECRET_KEY,
)
celery.conf.update(
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
    CELERY_ENABLE_UTC=True,
)


# Make a subclass of SQLAlchemyScheduler so we can override database_url
class DatabaseScheduler(SQLAlchemyScheduler):
    database_url = DATABASE_URL
    max_interval = 10
    sync_every = 10


@celery.task()
def add_together(a, b):
    return a + b


@celery.task()
def multiply(a, b):
    return a * b


# Don't show built-in celery tasks like 'chord', 'map', etc.
task_names = list(filter(
    lambda name: name.startswith('example_app.'),
    (name.replace('__main__.', 'example_app.') for name in celery.tasks.keys())
))


class PeriodicTaskView(ModelView):

    form_columns = [
        'name',
        'description',
        'task',
        'args',
        'kwargs',
        'interval_schedules',
        'crontab_schedules',
        'expires',
        'enabled',
        'queue',
        'exchange',
        'routing_key',
    ]
    form_overrides = dict(
        task=Select2Field,
    )
    form_args = dict(
        task=dict(
            choices=list(zip(task_names, task_names)),
        ),
    )

    column_list = [
        'name',
        'task',
        'args',
        'kwargs',
        'schedules',
        'expires',
        'last_run_at',
        'total_run_count',
        'enabled',
    ]

    def handle_view_exception(self, exc):
        if isinstance(exc, ValueError):
            exc = ValidationError(exc)
        return super(ModelView, self).handle_view_exception(exc)


class ScheduleView(ModelView):

    form_excluded_columns = ['periodic_tasks']

    def get_list_columns(self):
        return [
            ('description', self.get_column_name('description'))
        ] + super(ScheduleView, self).get_list_columns()


admin = Admin(
    flask,
    name='Celery Task Scheduler',
    template_mode='bootstrap3',
    url='/',
    index_view=PeriodicTaskView(
        PeriodicTask, session, endpoint='admin', name='Tasks',
    ),
)

admin.add_view(ScheduleView(IntervalSchedule, session, category='Schedules'))
admin.add_view(ScheduleView(CrontabSchedule, session, category='Schedules'))


if __name__ == '__main__':
    Base.metadata.create_all(session.bind)
    flask.run(debug=True)
