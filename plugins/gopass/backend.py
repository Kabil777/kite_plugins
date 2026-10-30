"""gopass CLI adapter; secrets travel only over stdin/stdout, never argv."""
import os
import shutil
import signal
import subprocess
import time


class BackendError(RuntimeError):
    pass


def _path(name, label):
    if (not isinstance(name, str) or not name or len(name) > 512 or name.startswith('/')
            or '\\' in name or '\0' in name or '\n' in name
            or any(part in ('', '.', '..') or part.startswith('-') for part in name.split('/'))):
        raise ValueError(f'Invalid gopass {label}')
    return name


def _run(*args, input_data=None, timeout=5, cancelled=lambda: False):
    binary = os.environ.get('GOPASS_BIN', 'gopass')
    if not shutil.which(binary):
        raise BackendError('gopass executable not found. Install gopass or set GOPASS_BIN.')
    if cancelled():
        raise BackendError('gopass operation cancelled.')
    try:
        with subprocess.Popen([binary, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, encoding='utf-8',
                              start_new_session=True) as process:
            deadline = time.monotonic() + timeout
            while True:
                stopped = cancelled()
                if stopped or time.monotonic() >= deadline:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.communicate()
                    raise BackendError('gopass operation cancelled.' if stopped else
                                       f'gopass timed out after {timeout} seconds. Check pinentry or SSH authentication.')
                try:
                    output, _ = process.communicate(input_data, timeout=min(.2, deadline - time.monotonic()))
                    break
                except subprocess.TimeoutExpired:
                    input_data = None
            if process.returncode == 11:
                raise BackendError('gopass decryption failed (exit 11); check GPG/age key access or pinentry.')
            if process.returncode:
                raise BackendError(f'gopass failed (exit {process.returncode}).')
            return output
    except OSError as error:
        raise BackendError('gopass could not be executed.') from error


def _store_path(entry, store):
    entry = _path(entry, 'entry')
    store = _path(store, 'store') if store else ''
    return f'{store}/{entry}' if store else entry


def entries(store='', cancelled=lambda: False):
    store = _path(store, 'store') if store else ''
    args = ['ls', '--flat']
    if store:
        args.extend(['--strip-prefix', store])
    return [line.strip() for line in _run(*args, cancelled=cancelled).splitlines() if line.strip()]


def password(entry, store='', cancelled=lambda: False):
    secret = _run('show', '--password', _store_path(entry, store),
                  timeout=120, cancelled=cancelled).rstrip('\n')
    if not secret or len(secret) > 4096:
        raise BackendError('gopass returned an empty or oversized password.')
    return secret


def create_entry(entry, secret, store='', cancelled=lambda: False):
    path = _store_path(entry, store)
    if not isinstance(secret, str) or not secret or len(secret) > 4096 or '\0' in secret:
        raise ValueError('Password must contain 1–4096 characters and no NUL bytes')
    if entry in entries(store, cancelled):
        raise BackendError('That gopass entry already exists.')
    _run('insert', path, input_data=secret, timeout=120, cancelled=cancelled)


def has_remote(store='', cancelled=lambda: False):
    args = ['git']
    if store:
        args.extend(['--store', _path(store, 'store')])
    return bool(_run(*args, 'remote', cancelled=cancelled).strip())


def sync(store='', cancelled=lambda: False):
    if not has_remote(store, cancelled):
        raise BackendError('No Git remote configured for this store.')
    args = ['sync']
    if store:
        args.extend(['--store', _path(store, 'store')])
    _run(*args, timeout=120, cancelled=cancelled)


if __name__ == '__main__':
    # Runnable adapter check; mocks all CLI calls and never accesses a real store.
    from unittest.mock import patch
    with patch(__name__ + '._run', return_value='fixture-only\n') as run:
        assert password('example.com/p1', 'work') == 'fixture-only'
        assert run.call_args.args == ('show', '--password', 'work/example.com/p1')
        assert run.call_args.kwargs['timeout'] == 120
    with patch(__name__ + '.entries', return_value=[]), patch(__name__ + '._run') as run:
        create_entry('example.com/p2', 'fixture-only')
        assert run.call_args.kwargs['input_data'] == 'fixture-only'
        assert run.call_args.kwargs['timeout'] == 120
    print('Gopass adapter check OK; no real credentials accessed')
