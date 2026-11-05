"""Configured local wallpaper files and one explicit awww request; no daemon management."""
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
from plugin_api import validate_settings

try:
    with Path(__file__).with_name('plugin.json').open(encoding='utf-8') as stream:
        contents = stream.read(16385)
    if len(contents) > 16384:
        raise ValueError('Manifest exceeds 16 KiB')
    FIELDS = json.loads(contents)['configuration']
    OPTION_FIELDS = [field for field in FIELDS if field['key'] != 'directories']
except (OSError, ValueError, KeyError, TypeError) as error:
    raise RuntimeError('Wallpaper package metadata is damaged; restore the reviewed package.') from error

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
    try:
        values = validate_settings([FIELDS[0]], {'directories': value})['directories']
    except (ValueError, RecursionError) as error:
        raise WallpaperError('Wallpaper folders need repair. Use Add/Browse in Plugin Settings.') from error
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


def option_args(options):
    try:
        values = validate_settings(OPTION_FIELDS, options)
    except ValueError as error:
        raise WallpaperError(str(error)) from error
    args = []
    for name in ('resize', 'crop_gravity', 'fill_color', 'filter', 'transition_type', 'transition_duration',
                 'transition_step', 'transition_fps', 'transition_angle'):
        data = values[name]
        if data is not None:
            if name == 'fill_color':
                data = data.lstrip('#')
            args.append('--' + name.replace('_', '-') + '=' + str(data))
    if values['crop_gravity'] is not None:
        if values['resize'] not in (None, 'crop'):
            raise WallpaperError('Crop position requires crop resize mode.')
        if values['resize'] is None:
            args.append('--resize=crop')
    position = values['position']
    coordinates = values['position_x'], values['position_y']
    if position in ('custom-fraction', 'custom-pixels'):
        if any(number is None for number in coordinates):
            raise WallpaperError('Custom transition position needs both X and Y.')
        if position == 'custom-fraction':
            if any(not 0 <= number <= 1 for number in coordinates):
                raise WallpaperError('Fraction positions must be between 0 and 1.')
            text = ','.join(format(number, '.6f') for number in coordinates)
        else:
            if any(int(number) != number for number in coordinates):
                raise WallpaperError('Pixel positions must be whole numbers.')
            text = ','.join(str(int(number)) for number in coordinates)
        args.append('--transition-pos=' + text)
    elif position is not None:
        args.append('--transition-pos=' + position)
    elif any(number is not None for number in coordinates):
        raise WallpaperError('Choose a custom position mode before setting X/Y.')
    for names, flag in ((('bezier_x1', 'bezier_y1', 'bezier_x2', 'bezier_y2'), 'transition-bezier'),
                        (('wave_width', 'wave_height'), 'transition-wave')):
        numbers = [values[name] for name in names]
        if any(number is not None for number in numbers):
            if any(number is None for number in numbers):
                raise WallpaperError('Set all ' + flag + ' coordinates together.')
            if flag == 'transition-bezier' and not any(numbers):
                raise WallpaperError('The all-zero Bézier curve is invalid; use 0,0,1,1 for linear.')
            args.append('--' + flag + '=' + ','.join(str(number) for number in numbers))
    environment = None
    if values['invert_y'] is not None:
        environment = {**os.environ, 'INVERT_Y': 'true' if values['invert_y'] else 'false'}
    if values['invert_y']:
        args.append('--invert-y')
    return args, environment


def apply(wallpaper, roots, cancelled=lambda: False, options=None):
    path = validate(wallpaper, roots)
    args, environment = option_args(options or {})
    executable = shutil.which('awww')
    if executable is None:
        raise WallpaperError('awww is not installed. Install it and start awww-daemon in your Wayland session.')
    if cancelled():
        raise WallpaperError('Wallpaper change cancelled before sending a request.')
    try:
        # No --outputs means all outputs in the normal daemon namespace, not all daemon instances.
        subprocess.run([executable, 'img', *args, '--', str(path)], check=True, timeout=5, env=environment,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as error:
        raise WallpaperError('awww timed out; the wallpaper may already have changed. Check before retrying.') from error
    except subprocess.CalledProcessError as error:
        raise WallpaperError('awww could not finish. Check the image is valid and awww-daemon is running in this session; some outputs may have changed.') from error
    except OSError as error:
        raise WallpaperError('Could not start awww. Check its installation and your Wayland session.') from error
