from celery import Celery, shared_task, Task as CelTask
from dotenv import load_dotenv
from os import getenv
import subprocess
import os
import shutil
import pathlib
from collections import namedtuple
from db import db
from models import Submission, SubmissionStatus
import logging
from flask import Flask
load_dotenv()

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(CelTask):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

@shared_task(ignore_result=False)
def run_judge(tests: list, upload_directory: str, submission_directory: str, timeout: int, mem: int, submission_id: str):
    host_uploads = os.environ.get('HOST_UPLOADS')
    mem_kb = mem * 1024
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
        str(timeout), str(mem_kb)        
    ], text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    if docker_tester.returncode != 0:
        compile_text = ""
        compile_log = pathlib.Path(upload_directory) / 'compile.log'
        if compile_log.exists():
            compile_text = compile_log.read_text()
            
        sub = db.session.get(Submission, submission_id)
        sub.status = SubmissionStatus.COMPILATION_ERROR
        sub.error_message = compile_text
        db.session.commit()
        
        return [], SubmissionStatus.COMPILATION_ERROR.value, 0, compile_text, '', ''

    results = []
    passed = 0
    re_details = []
    
    results_csv = pathlib.Path(upload_directory) / 'results.csv'
    raw_metrics = {}
    if results_csv.exists():
        for line in results_csv.read_text().strip().splitlines():
            parts = line.split(',')
            if len(parts) == 3:
                try:
                    mem_val = int(parts[2])
                except ValueError:
                    mem_val = 0
                raw_metrics[int(parts[0])] = {'exit': int(parts[1]), 'mem': mem_val}

    for test_number, _ in enumerate(tests, start=1):
        test_metrics = raw_metrics.get(test_number)
        out_path = pathlib.Path(upload_directory) / f'{test_number}.out'
        ans_path = pathlib.Path(upload_directory) / f'{test_number}.ans'
        
        verdict = SubmissionStatus.RUNTIME_ERROR.value
        
        if test_metrics:
            ec = test_metrics['exit']
            mem_used = test_metrics['mem']
            
            if ec in (124, 143, 15): 
                verdict = SubmissionStatus.MEMORY_LIMIT.value if mem_used >= mem_kb else SubmissionStatus.TIME_LIMIT.value
            elif ec in (137, 9) or mem_used >= mem_kb:
                verdict = SubmissionStatus.MEMORY_LIMIT.value
            elif ec != 0:
                verdict = SubmissionStatus.RUNTIME_ERROR.value
                re_details.append(f"Test {test_number}: RE (exit code {ec})")
            elif not out_path.exists():
                verdict = SubmissionStatus.RUNTIME_ERROR.value
                re_details.append(f"Test {test_number}: RE (No output file)")
            else:
                out = out_path.read_text().strip()
                ans = ans_path.read_text().strip()
                verdict = SubmissionStatus.OK.value if out == ans else SubmissionStatus.WRONG_ANSWER.value

        if verdict == SubmissionStatus.OK.value:
            passed += 1
            
        results.append({
            'test': test_number,
            'verdict': verdict,
        })

    error_log = "\n".join(re_details) if re_details else ""
    total = len(tests)
    
    if passed == total:
        verdict = SubmissionStatus.OK.value
    elif passed == 0:
        verdict = results[0]['verdict'] if results else SubmissionStatus.RUNTIME_ERROR.value
    else:
        verdict = SubmissionStatus.PARTIAL_SOLUTION.value

    sub = db.session.get(Submission, submission_id)
    sub.status = SubmissionStatus(verdict)
    sub.passed_tests = passed
    sub.error_message = error_log
    db.session.commit()
    shutil.rmtree(upload_directory, ignore_errors=True)
    return verdict, passed, error_log, docker_tester.stderr, docker_tester.stdout