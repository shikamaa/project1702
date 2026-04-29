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
def parse_metrics(metrics_path):
    if not metrics_path.exists():
        return 0, 0, 1

    text = metrics_path.read_text()

    time_match = re.search(r'Elapsed.*?: (\d+):(\d+)\.(\d+)', text)
    if time_match:
        minutes = int(time_match.group(1))
        seconds = int(time_match.group(2))
        centiseconds = int(time_match.group(3))
        elapsed_ms = (minutes * 60 + seconds + centiseconds / 100) * 1000
    else:
        elapsed_ms = 0

    mem_match = re.search(r'Maximum resident set size.*?: (\d+)', text)
    memory_kb = int(mem_match.group(1)) if mem_match else 0

    exit_match = re.search(r'EXIT:(\d+)', text)
    exit_code = int(exit_match.group(1)) if exit_match else 1

    return elapsed_ms, memory_kb, exit_code


@shared_task(ignore_result=False)
def run_judge(tests, upload_directory, submission_directory, timeout, mem):
    host_uploads = os.environ.get('HOST_UPLOADS')

    docker_tester = subprocess.run([
        'timeout', '240',
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

    compile_log = pathlib.Path(upload_directory) / 'compile.log'
    if compile_log.exists() and compile_log.read_text().strip():
        return [], 'CE'

    results = []
    passed = 0

    for test_number, _ in enumerate(tests, start=1):
        out_path = pathlib.Path(upload_directory) / f'{test_number}.out'
        ans_path = pathlib.Path(upload_directory) / f'{test_number}.ans'
        metrics_path = pathlib.Path(upload_directory) / f'{test_number}.metrics'

        elapsed_ms, memory_kb, exit_code = parse_metrics(metrics_path)

        if exit_code == 124:
            verdict = 'TLE'
        elif exit_code != 0:
            verdict = 'RTE'
        elif not out_path.exists():
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
            'time_ms': elapsed_ms,
            'mem_kb':  memory_kb,
        })

    total = len(tests)
    if passed == total:
        final = 'OK'
    elif passed == 0:
        final = results[0]['verdict']
    else:
        final = 'PS'

    return results, final, passed