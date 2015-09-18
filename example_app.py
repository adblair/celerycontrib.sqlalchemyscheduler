
from celery import Celery
from celerycontrib.sqlalchemyscheduler import model, SQLAlchemyScheduler
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BROKER_URL = 'amqp://guest@localhost//'
DATABASE_URL = 'sqlite:///example.sqlite'
SECRET_KEY = '0123456789'

flask = Flask(__name__)
admin = Admin(flask, name='Celery Scheduler', template_mode='bootstrap3')
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


class PeriodicTaskView(ModelView):
    # inline_models = [model.IntervalSchedule, model.CrontabSchedule]
    pass

admin.add_view(PeriodicTaskView(model.PeriodicTask, session))


# Make a subclass of SQLAlchemyScheduler so we can override database_url
class DatabaseScheduler(SQLAlchemyScheduler):
    database_url = DATABASE_URL
    max_interval = 10
    sync_every = 10


@celery.task()
def add_together(a, b):
    return a + b


if __name__ == '__main__':
    model.Base.metadata.create_all(session.bind)
    flask.run(debug=True)
