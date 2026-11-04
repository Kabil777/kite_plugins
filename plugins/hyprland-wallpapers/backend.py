"""Configured local wallpaper files and one explicit awww request; no daemon management."""
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff', '.avif'}
MAX_IMAGES = 2000
MAX_ENTRIES = 10000
MAX_BYTES = 32 * 1024 * 1024


class WallpaperError(ValueError):
    pass


@dataclass(frozen=True)
class Wallpaper:
    path: Path
    fingerprint: tuple

    @property
    def id(self):
        return 'wallpaper:' + sha256(os.fsencode(self.path) + repr(self.fingerprint).encode()).hexdigest()


def signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def directories(value):
    if not isinstance(value, str) or len(value) > 1024:
        raise WallpaperError('Use a JSON folder list of at most 1,024 characters in Plugin Settings, for example ["~/Pictures/Wallpapers"].')
    try:
        values = json.loads(value)
    except (ValueError, RecursionError) as error:
        raise WallpaperError('Use a JSON list of folders, for example ["~/Pictures/Wallpapers"].') from error
    if (not isinstance(values, list) or len(values) > 16
            or any(not isinstance(item, str) or not item.strip() or '\0' in item for item in values)):
        raise WallpaperError('Use a JSON list containing up to 16 nonempty folder paths.')
    roots, warnings = [], []
    for value in values:
        try:
            value.encode('utf-8')
        except UnicodeError as error:
            raise WallpaperError('Folder paths must use valid UTF-8 text.') from error
        try:
            path = Path(value).expanduser()
        except RuntimeError as error:
            raise WallpaperError('Could not expand that home-folder path; use an absolute path instead.') from error
        if not path.is_absolute():
            raise WallpaperError('Use absolute folder paths or ~/ paths, not relative paths.')
        try:
            path = path.resolve(strict=True)
            if not path.is_dir():
                raise OSError('not a directory')
        except (OSError, RuntimeError):
            warnings.append('Folder unavailable: ' + value)
            continue
        if path not in roots:
            roots.append(path)
    return tuple(roots), tuple(warnings)


def checked_file(path, roots):
    try:
        if path.is_symlink():
            raise WallpaperError('Wallpaper symlinks are not followed; choose an image inside a configured folder.')
        resolved = path.resolve(strict=True)
        if not any(resolved.is_relative_to(root) for root in roots):
            raise WallpaperError('Wallpaper is outside the configured folders.')
        str(resolved).encode('utf-8')
        info = resolved.stat()
        if (not stat.S_ISREG(info.st_mode) or resolved.suffix.casefold() not in EXTENSIONS
                or not 0 < info.st_size <= MAX_BYTES or len(str(resolved)) > 4096):
            raise WallpaperError('Choose a supported regular image file, at most 32 MiB.')
        return resolved, info
    except (OSError, RuntimeError, UnicodeError) as error:
        raise WallpaperError('Wallpaper is no longer available. Refresh the list.') from error


def scan(roots, cancelled=lambda: False):
    pending, seen, images = list(reversed(roots)), set(), []
    examined, skipped, limited = 0, 0, False
    while pending and not limited:
        if cancelled():
            raise WallpaperError('Wallpaper scan cancelled')
        directory = pending.pop()
        try:
            directory = directory.resolve(strict=True)
            if directory in seen or not any(directory.is_relative_to(root) for root in roots):
                continue
            seen.add(directory)
            with os.scandir(directory) as entries:
                for entry in entries:
                    if cancelled():
                        raise WallpaperError('Wallpaper scan cancelled')
                    examined += 1
                    if examined > MAX_ENTRIES or len(images) >= MAX_IMAGES:
                        limited = True
                        break
                    if entry.name.startswith('.') or entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
                    elif Path(entry.name).suffix.casefold() in EXTENSIONS:
                        try:
                            path, info = checked_file(Path(entry.path), roots)
                        except WallpaperError:
                            skipped += 1
                            continue
                        images.append(Wallpaper(path, signature(info)))
        except (OSError, RuntimeError):
            skipped += 1
    images.sort(key=lambda item: (item.path.name.casefold(), str(item.path)))
    warning = 'Scan limit reached; use narrower folders.' if limited else ''
    if skipped:
        warning += (' ' if warning else '') + f'{skipped} unavailable/unsupported items skipped.'
    return tuple(images), warning


def validate(wallpaper, roots):
    path, info = checked_file(wallpaper.path, roots)
    if signature(info) != wallpaper.fingerprint:
        raise WallpaperError('Wallpaper changed since it was listed. Refresh and preview it again.')
    return path


def apply(wallpaper, roots, cancelled=lambda: False):
    path = validate(wallpaper, roots)
    executable = shutil.which('awww')
    if executable is None:
        raise WallpaperError('awww is not installed. Install it and start awww-daemon in your Wayland session.')
    if cancelled():
        raise WallpaperError('Wallpaper change cancelled before sending a request.')
    try:
        # No --outputs means all outputs in the normal daemon namespace, not all daemon instances.
        subprocess.run([executable, 'img', '--', str(path)], check=True, timeout=5,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as error:
        raise WallpaperError('awww timed out; the wallpaper may already have changed. Check before retrying.') from error
    except subprocess.CalledProcessError as error:
        raise WallpaperError('awww could not finish. Check the image is valid and awww-daemon is running in this session; some outputs may have changed.') from error
    except OSError as error:
        raise WallpaperError('Could not start awww. Check its installation and your Wayland session.') from error
