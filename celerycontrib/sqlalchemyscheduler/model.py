"""Adapted from djcelery.models."""

import datetime

import celery.schedules
import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.ext import declarative


class Base(object):
    id = sqla.Column(sqla.Integer, primary_key=True)

Base = declarative.declarative_base(cls=Base)


class IntervalSchedule(Base):

    __tablename__ = 'interval_schedule'

    every = sqla.Column(sqla.Integer, nullable=False)
    period = sqla.Column(sqla.String(24))

    @property
    def schedule(self):
        return celery.schedules.schedule(
            datetime.timedelta(**{self.period: self.every})
        )

    def __str__(self):
        if self.every == 1:
            return 'every {0.period_singular}'.format(self)
        return 'every {0.every} {0.period}'.format(self)

    @property
    def period_singular(self):
        return self.period[:-1]


class CrontabSchedule(Base):

    __tablename__ = 'crontab_schedule'

    minute = sqla.Column(sqla.String(64), default='*')
    hour = sqla.Column(sqla.String(64), default='*')
    day_of_week = sqla.Column(sqla.String(64), default='*')
    day_of_month = sqla.Column(sqla.String(64), default='*')
    month_of_year = sqla.Column(sqla.String(64), default='*')

    def __str__(self):
        rfield = lambda f: f and str(f).replace(' ', '') or '*'
        return '{0} {1} {2} {3} {4} (m/h/d/dM/MY)'.format(
            rfield(self.minute), rfield(self.hour), rfield(self.day_of_week),
            rfield(self.day_of_month), rfield(self.month_of_year),
        )

    @property
    def schedule(self):
        return celery.schedules.crontab(
            minute=self.minute,
            hour=self.hour,
            day_of_week=self.day_of_week,
            day_of_month=self.day_of_month,
            month_of_year=self.month_of_year,
        )


class PeriodicTask(Base):

    __tablename__ = 'periodic_task'

    name = sqla.Column(
        sqla.String(200),
        unique=True,
        doc='Useful description',
    )
    task = sqla.Column(sqla.String(200), doc='Task name')
    interval_schedule_id = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('interval_schedule.id'),
        nullable=True,
    )
    interval_schedule = orm.relationship(
        'IntervalSchedule',
        backref=orm.backref('periodic_task', uselist=False),
    )
    crontab_schedule_id = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('crontab_schedule.id'),
        nullable=True,
    )
    crontab_schedule = orm.relationship(
        'CrontabSchedule',
        backref=orm.backref('periodic_task', uselist=False),
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

    def __str__(self):
        fmt = '{0.name}: {{no schedule}}'
        if self.interval_schedule:
            fmt = '{0.name}: {0.interval_schedule}'
        if self.crontab_schedule:
            fmt = '{0.name}: {0.crontab_schedule}'
        return fmt.format(self)

    @property
    def schedule(self):
        if self.interval_schedule:
            return self.interval_schedule
        if self.crontab_schedule:
            return self.crontab_schedule
