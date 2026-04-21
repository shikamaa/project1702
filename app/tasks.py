from celery import Celery, shared_task, Task
from celery.result import AsyncResult
from dotenv import load_dotenv
from os import getenv
from flask import Flask

load_dotenv()  # добавь это

celery = Celery('__main__', broker=getenv('REDIS_URL'), backend=getenv('REDIS_URL'))

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


@shared_task(ignore_result=False)
def test(param):
    return param * 2


@shared_task(ignore_result=False, bind=True)
def run_judge(self,tests):
    for i in tests:
        print(i)