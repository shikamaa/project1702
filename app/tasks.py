from celery import Celery, shared_task, Task
from celery.result import AsyncResult
from dotenv import load_dotenv
from os import getenv
from flask import Flask
import subprocess
import os
import shutil
import pathlib
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


# @shared_task(ignore_result=False, bind=True)
# def run_judge(self,tests):
@shared_task(ignore_result=False)
def run_judge(tests, upload_directory,submission_directory):
    docker_tester = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{os.environ.get('HOST_UPLOADS')}:/uploads",
            "--network=none",
            "judge",
            "sh", f"/uploads/{submission_directory}/s.sh", f"/uploads/{submission_directory}/solution.c",
    ], text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    print(docker_tester.stdout)
    print(docker_tester.stderr)
    print(docker_tester.returncode)
    for test_number, test_case in enumerate(tests, start=1):
        out_path = pathlib.Path(upload_directory) / f"{test_number}.out"
        ans_path = pathlib.Path(upload_directory) / f"{test_number}.ans"
        var = (

        )
        out = out_path.read_text().strip()
        ans = ans_path.read_text().strip()
        results = []
        if out == ans:
            #print(f"Test {test_number}: AC")
            var = (test_number, "AC")
            results.append(var)
        else:
            # print(f"Test {test_number}: WA | got: {out} | expected: {ans}")
            var = (test_number, f"got: {out}, expected: {ans}")
            results.append(var)
    return results