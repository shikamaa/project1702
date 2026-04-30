from celery import Celery, shared_task, Task
from celery.result import AsyncResult
from dotenv import load_dotenv
from os import getenv
from flask import Flask
import subprocess
import os
import shutil
import pathlib
from collections import namedtuple
import re


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
# tasks.py
@shared_task(ignore_result=False)
def run_judge(tests, upload_directory, submission_directory, timeout, mem):
    host_uploads = os.environ.get('HOST_UPLOADS')
    docker_tester = subprocess.run([
        'docker', 'run', '--rm',
        '--network=none',
        '--memory', f'{mem}m',
        '--memory-swap', f'{mem}m',
        '--pids-limit', '64',
        '--cpus', '1',
        '-v', f'{host_uploads}:/uploads',
        'judge',
        'sh', f'/uploads/{submission_directory}/s.sh',
        f'/uploads/{submission_directory}/solution.c',
    ], text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    print(docker_tester.stderr)
    print(docker_tester.stdout)
    compile_log = pathlib.Path(upload_directory) / 'compile.log'
    if compile_log.exists() and compile_log.read_text().strip():
        return [], 'CE', 0, '', ''
    results = []
    passed = 0
    for test_number, _ in enumerate(tests, start=1):
        out_path = pathlib.Path(upload_directory) / f'{test_number}.out'
        ans_path = pathlib.Path(upload_directory) / f'{test_number}.ans'
        if not out_path.exists():
            verdict = 'RTE'
        else:
            out = out_path.read_text().strip()
            ans = ans_path.read_text().strip()
            verdict = 'AC' if out == ans else 'WA'
            if verdict == 'AC':
                passed += 1
        results.append({
            'test':    test_number,
            'verdict': verdict,
        })
    total = len(tests)
    if passed == total:
        final = 'OK'
    elif passed == 0:
        final = results[0]['verdict']
    else:
        final = 'PS'
    return results, final, passed, docker_tester.stderr, docker_tester.stdout