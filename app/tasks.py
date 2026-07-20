from celery import Celery, shared_task, Task as CelTask
from celery.utils.log import get_task_logger
from dotenv import load_dotenv
import os
import shutil
import pathlib
from db import db
from models import Submission, SubmissionStatus
from flask import Flask
import docker
import requests

load_dotenv()
logger = get_task_logger(__name__)

MAX_OUT_BYTES = 5 * 1024 * 1024
MAX_ERR_LEN = 4000


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


def _finish(submission_id, status, passed=0, error_message=""):
    """Единая точка записи результата в БД."""
    sub = db.session.get(Submission, submission_id)
    if sub:
        sub.status = status
        sub.passed_tests = passed
        sub.error_message = error_message[:MAX_ERR_LEN]
        db.session.commit()
    return status.value, passed, error_message


@shared_task(ignore_result=False)
def run_judge(tests: list, upload_directory: str, submission_directory: str,
              timeout: int, mem: int, submission_id: str):
    host_uploads = os.environ.get('HOST_UPLOADS')
    mem_kb = mem * 1024

    container_mem = max(mem + 128, 256)

    budget = 10 + len(tests) * (timeout + 1) + 10

    container = None
    try:
        docker_tester = docker.from_env()
        container = docker_tester.containers.run(
            'judge',
            detach=True,
            network_disabled=True,
            volumes={f'{host_uploads}/{submission_directory}': {'bind': '/uploads', 'mode': 'rw'}},
            mem_limit=f'{container_mem}m',
            memswap_limit=f'{container_mem}m',
            nano_cpus=1_000_000_000,
            pids_limit=64,
            user='nobody',
            cap_drop=['ALL'],
            security_opt=['no-new-privileges'],
            command=['sh', '/uploads/s.sh', '/uploads/solution.c',
                     str(timeout), str(mem_kb)],
        )

        try:
            exit_code = container.wait(timeout=budget).get('StatusCode', 1)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            logger.error("judge exceeded budget %ss for submission %s", budget, submission_id)
            return _finish(submission_id, SubmissionStatus.CHECK_FAILED,
                           0, "judge time budget exceeded")

        if exit_code == 1:
            compile_text = ""
            compile_log = pathlib.Path(upload_directory) / 'compile.log'
            if compile_log.exists():
                compile_text = compile_log.read_text(errors='replace')
            compile_text = compile_text.replace('/uploads/', '')
            return _finish(submission_id, SubmissionStatus.COMPILATION_ERROR,
                           0, compile_text or "compilation failed")

        if exit_code != 0:
            logger.error("judge script exited with %s for submission %s",
                         exit_code, submission_id)
            return _finish(submission_id, SubmissionStatus.CHECK_FAILED,
                           0, "judge internal error")

        raw_metrics = {}
        results_csv = pathlib.Path(upload_directory) / 'results.csv'
        if results_csv.exists():
            for line in results_csv.read_text(errors='replace').strip().splitlines():
                parts = line.split(',')
                if len(parts) != 3:
                    continue
                try:
                    raw_metrics[int(parts[0])] = {'exit': int(parts[1]),
                                                  'mem': int(parts[2])}
                except ValueError:
                    continue

        results = []
        passed = 0
        re_details = []

        for test_number, test_case in enumerate(tests, start=1):
            test_metrics = raw_metrics.get(test_number)
            out_path = pathlib.Path(upload_directory) / f'{test_number}.out'

            verdict = SubmissionStatus.RUNTIME_ERROR.value

            if test_metrics:
                ec = test_metrics['exit']
                mem_used = test_metrics['mem']

                if ec in (124, 143, 15):
                    verdict = (SubmissionStatus.MEMORY_LIMIT.value
                               if mem_used >= mem_kb
                               else SubmissionStatus.TIME_LIMIT.value)
                elif ec in (137, 9) or mem_used >= mem_kb:
                    verdict = SubmissionStatus.MEMORY_LIMIT.value
                elif ec == 153:
                    verdict = SubmissionStatus.RUNTIME_ERROR.value
                    re_details.append(f"Test {test_number}: RE (output limit exceeded)")
                elif ec != 0:
                    verdict = SubmissionStatus.RUNTIME_ERROR.value
                    re_details.append(f"Test {test_number}: RE (exit code {ec})")
                elif not out_path.exists():
                    verdict = SubmissionStatus.RUNTIME_ERROR.value
                    re_details.append(f"Test {test_number}: RE (No output file)")
                elif out_path.stat().st_size > MAX_OUT_BYTES:
                    verdict = SubmissionStatus.RUNTIME_ERROR.value
                    re_details.append(f"Test {test_number}: RE (output too large)")
                else:
                    out = out_path.read_text(errors='replace').strip()
                    ans = str(test_case.get("output") or "").strip()
                    verdict = (SubmissionStatus.OK.value if out == ans
                               else SubmissionStatus.WRONG_ANSWER.value)

            if verdict == SubmissionStatus.OK.value:
                passed += 1

            results.append({'test': test_number, 'verdict': verdict})

        error_log = "\n".join(re_details) if re_details else ""
        total = len(tests)

        if passed == total:
            verdict = SubmissionStatus.OK.value
        elif passed == 0:
            verdict = results[0]['verdict'] if results else SubmissionStatus.RUNTIME_ERROR.value
        else:
            verdict = SubmissionStatus.PARTIAL_SOLUTION.value

        return _finish(submission_id, SubmissionStatus(verdict), passed, error_log)

    except docker.errors.ImageNotFound:
        logger.error("Judge image not found — run: docker compose --profile build-only build")
        return _finish(submission_id, SubmissionStatus.REJECTED, 0, "judge image missing")

    except docker.errors.APIError as ae:
        logger.error("Docker API error: %s", ae)
        return _finish(submission_id, SubmissionStatus.REJECTED, 0, "docker api error")

    except Exception:
        logger.exception("judge task failed for submission %s", submission_id)
        db.session.rollback()
        sub = db.session.get(Submission, submission_id)
        if sub:
            sub.status = SubmissionStatus.CHECK_FAILED
            db.session.commit()
        raise

    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except docker.errors.APIError:
                pass
        shutil.rmtree(upload_directory, ignore_errors=True)