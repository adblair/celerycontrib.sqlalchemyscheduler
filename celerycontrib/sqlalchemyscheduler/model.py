"""Adapted from djcelery.models."""

import collections
import datetime
import itertools
import json

import celery.schedules
import pretty_cron
import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.ext import declarative


class Base(object):
    id = sqla.Column(sqla.Integer, primary_key=True)

Base = declarative.declarative_base(cls=Base)


class IntervalSchedule(Base):

    __tablename__ = 'interval_schedule'

    every = sqla.Column(sqla.Integer, nullable=False)
    period = sqla.Column(sqla.String(24), nullable=False)

    @property
    def schedule(self):
        return celery.schedules.schedule(
            datetime.timedelta(**{self.period: self.every})
        )

    @property
    def period_singular(self):
        return self.period[:-1]

    @property
    def description(self):
        if self.every == 1:
            return 'every {0.period_singular}'.format(self)
        return 'every {0.every} {0.period}'.format(self)

    def __str__(self):
        return self.description


class CrontabSchedule(Base):

    __tablename__ = 'crontab_schedule'

    minute = sqla.Column(sqla.String(64), default='*')
    hour = sqla.Column(sqla.String(64), default='*')
    day_of_week = sqla.Column(sqla.String(64), default='*')
    day_of_month = sqla.Column(sqla.String(64), default='*')
    month_of_year = sqla.Column(sqla.String(64), default='*')

    @property
    def description(self):
        rfield = lambda f: f and str(f).replace(' ', '') or '*'
        string = '{0} {1} {2} {3} {4}'.format(
            rfield(self.minute), rfield(self.hour), rfield(self.day_of_week),
            rfield(self.day_of_month), rfield(self.month_of_year),
        )
        return pretty_cron.prettify_cron(string)

    @property
    def schedule(self):
        return celery.schedules.crontab(
            minute=self.minute,
            hour=self.hour,
            day_of_week=self.day_of_week,
            day_of_month=self.day_of_month,
            month_of_year=self.month_of_year,
        )

    def __str__(self):
        return self.description


class PeriodicTask(Base):

    __tablename__ = 'periodic_task'

    name = sqla.Column(
        sqla.String(200),
        unique=True,
        doc='Useful description',
        nullable=False,
    )
    task = sqla.Column(
        sqla.String(200),
        doc='Task name',
        nullable=False,
    )
    interval_schedules = orm.relationship(
        'IntervalSchedule',
        secondary='task_interval_schedules',
        backref='periodic_tasks',
    )
    crontab_schedules = orm.relationship(
        'CrontabSchedule',
        secondary='task_crontab_schedules',
        backref='periodic_tasks',
    )
    args = sqla.Column(
        sqla.String,
        nullable=True,
        default='[]',
        doc='JSON encoded positional arguments',
    )
    kwargs = sqla.Column(
        sqla.String,
        nullable=True,
        default='{}',
        doc='JSON encoded keyword arguments',
    )
    queue = sqla.Column(
        sqla.String(200),
        nullable=True,
        default=None,
        doc='Queue defined in CELERY_QUEUES',
    )
    exchange = sqla.Column(
        sqla.String(200),
        nullable=True,
        default=None,
    )
    routing_key = sqla.Column(
        sqla.String(200),
        nullable=True,
        default=None,
    )
    expires = sqla.Column(sqla.DateTime, nullable=True)
    enabled = sqla.Column(sqla.Boolean, default=True)
    last_run_at = sqla.Column(sqla.DateTime, nullable=True)
    total_run_count = sqla.Column(sqla.Integer, default=0)
    date_changed = sqla.Column(
        sqla.DateTime,
        server_default=sqla.func.now(),
        onupdate=sqla.func.now(),
    )
    description = sqla.Column(sqla.String, nullable=True)

    @property
    def schedules(self):
        return list(
            itertools.chain(self.interval_schedules, self.crontab_schedules)
        )

    @orm.validates('args')
    def validate_args(self, key, value):
        return _validate_json_string(
            value, collections.Sequence, 'kwargs must be a valid JSON array'
        )

    @orm.validates('kwargs')
    def validate_kwargs(self, key, value):
        return _validate_json_string(
            value, collections.Mapping, 'kwargs must be a valid JSON object'
        )

    def __str__(self):
        return self.name


task_interval_schedules = sqla.Table(
    'task_interval_schedules', Base.metadata,
    sqla.Column(
        'periodic_task_id',
        sqla.Integer,
        sqla.ForeignKey('periodic_task.id'),
    ),
    sqla.Column(
        'interval_schedule_id',
        sqla.Integer,
        sqla.ForeignKey('interval_schedule.id'),
    )
)

task_crontab_schedules = sqla.Table(
    'task_crontab_schedules', Base.metadata,
    sqla.Column(
        'periodic_task_id',
        sqla.Integer,
        sqla.ForeignKey('periodic_task.id'),
    ),
    sqla.Column(
        'crontab_schedule_id',
        sqla.Integer,
        sqla.ForeignKey('crontab_schedule.id'),
    )
)


def _validate_json_string(string, cls, msg, nullable=True):
    if nullable and string is None:
        return string
    try:
        obj = json.loads(string)
    except Exception:
        raise ValueError(msg)
    else:
        if not isinstance(obj, cls):
            raise ValueError(msg)
        else:
            return string
