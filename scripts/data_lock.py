from contextlib import contextmanager
import fcntl
from pathlib import Path

@contextmanager
def data_lock():
    target=Path(__file__).resolve().parents[1]/'data/.update.lock'
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('a') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another data update is running. Wait for it to finish; do not run imports/geocoding in parallel.')
        yield
