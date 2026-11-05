"""Wallpaper contracts, indexing and fake awww only. Native UI is checked by KITE's catalog test."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'plugins' / 'hyprland-wallpapers'
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg==')


def main():
    with tempfile.TemporaryDirectory(prefix='kite-wallpapers-') as temporary:
        temp = Path(temporary)
        binary = temp / 'bin'
        binary.mkdir()
        log = temp / 'requests.jsonl'
        fake = binary / 'awww'
        fake.write_text(f'#!{sys.executable}\nimport json, os, sys\n'
                        'with open(os.environ["WALLPAPER_TEST_LOG"], "a") as stream:\n'
                        '    stream.write(json.dumps(sys.argv[1:]) + "\\n")\n'
                        'sys.exit(int(os.environ.get("WALLPAPER_TEST_EXIT", "0")))\n')
        fake.chmod(0o700)
        env = {'HOME': str(temp), 'PATH': str(binary), 'WALLPAPER_TEST_LOG': str(log)}
        for name in ('CONFIG', 'CACHE', 'DATA', 'RUNTIME'):
            path = temp / name.lower()
            path.mkdir(mode=0o700)
            env['XDG_' + name + ('_DIR' if name == 'RUNTIME' else '_HOME')] = str(path)
        with patch.dict(os.environ, env):
            from main.plugin_api import Event, HostServices, _load_plugin, validate_view, validate_toast
            from main.plugin_protocol import from_wire, to_wire
            manifest, plugin = _load_plugin(SOURCE)
            backend = sys.modules[plugin.__name__ + '.backend']
            assert manifest['configuration'][0]['type'] == 'directory_list'
            folder, nested = temp / 'images; not a shell', temp / 'images; not a shell' / 'nested'
            nested.mkdir(parents=True)
            first = folder / 'forest; touch unwanted.PNG'
            first.write_bytes(PNG)
            (nested / 'ocean.png').write_bytes(PNG)
            outside = temp / 'outside.png'
            outside.write_bytes(PNG)
            (folder / '.hidden.png').write_bytes(PNG)
            hidden = folder / '.hidden'
            hidden.mkdir()
            (hidden / 'private.png').write_bytes(PNG)
            (folder / 'linked.png').symlink_to(outside)
            (folder / 'linked-dir').symlink_to(temp, target_is_directory=True)
            (folder / 'empty.png').touch()
            with open(os.fsencode(folder) + b'/invalid-\xff.png', 'wb') as stream:
                stream.write(PNG)
            os.mkfifo(folder / 'pipe.png')
            with (folder / 'huge.png').open('wb') as stream:
                stream.truncate(backend.MAX_BYTES + 1)
            config = {'plugins': {'hyprland-wallpapers': {'config': {'directories': json.dumps([str(folder), str(nested), str(folder)])}}}}
            host = HostServices(config)
            view = plugin.search('', host)
            validate_view(view)
            assert from_wire(json.loads(json.dumps(to_wire(view)))) == view
            assert len(view.results) == 2 and view.catalog.layout == 'list_detail' and not view.nodes
            assert not view.catalog.settings_keys and not view.catalog.option_keys
            def configured(options):
                return HostServices({'plugins': {'hyprland-wallpapers': {'config': {
                    **config['plugins']['hyprland-wallpapers']['config'], **options}}}})
            assert len(plugin.search('nested ocean', host).results) == 1
            row = next(row for row in view.results if row.title == first.name)
            assert row.preview.props['source'] == str(first) and not row.action.push
            assert not log.exists(), 'Search/preview descriptors must not execute awww'
            for event in (Event('unknown', 'activate'), Event(row.id, 'submit'), Event(row.id, 'activate', {'query': []}),
                          Event(row.id, 'activate', {'settings': {'extra_args': ';touch pwn'}}),
                          Event(row.id, 'activate', {'settings': {'transition_type': 'fade'}})):
                failed = plugin.handle_event(event, host)
                validate_toast(failed)
                assert failed.tone == 'error' and not log.exists()
            result = plugin.handle_event(Event(row.id, 'activate', {'value': str(outside)}), host)
            assert result.toast.tone == 'success'
            assert json.loads(log.read_text().splitlines()[0]) == ['img', '--', str(first)]
            options = {'resize': 'crop', 'crop_gravity': 'top', 'fill_color': '#112233ff', 'filter': 'Nearest',
                       'transition_type': 'fade', 'transition_duration': .8, 'transition_step': 12, 'transition_fps': 60,
                       'transition_angle': -45, 'position': 'custom-fraction', 'position_x': 1, 'position_y': .5,
                       'bezier_x1': 0, 'bezier_y1': 0, 'bezier_x2': 1, 'bezier_y2': 1,
                       'wave_width': 20, 'wave_height': 25, 'invert_y': True}
            result = plugin.handle_event(Event(row.id, 'activate'), configured(options))
            assert result.toast.tone == 'success'
            args = json.loads(log.read_text().splitlines()[-1])
            for flag in ('--resize=crop', '--crop-gravity=top', '--fill-color=112233ff', '--filter=Nearest',
                         '--transition-type=fade', '--transition-duration=0.8', '--transition-step=12', '--transition-fps=60',
                         '--transition-angle=-45', '--transition-pos=1.000000,0.500000',
                         '--transition-bezier=0,0,1,1', '--transition-wave=20,25', '--invert-y'):
                assert flag in args, (flag, args)
            assert args[-2:] == ['--', str(first)] and '--all' not in args and '--outputs' not in args
            assert not (temp / 'unwanted.PNG').exists()
            args, environment = backend.option_args({'invert_y': False})
            assert not args and environment['INVERT_Y'] == 'false'
            args, _ = backend.option_args({'position': 'custom-pixels', 'position_x': 200, 'position_y': 400})
            assert '--transition-pos=200,400' in args
            for invalid in ({'transition_fps': 0}, {'transition_step': True}, {'transition_duration': float('nan')},
                            {'resize': 'fit', 'crop_gravity': 'top'}, {'position': 'custom-fraction', 'position_x': 2, 'position_y': 0},
                            {'position': 'custom-pixels', 'position_x': .5, 'position_y': 1}, {'bezier_x1': 1},
                            {'bezier_x1': 0, 'bezier_y1': 0, 'bezier_x2': 0, 'bezier_y2': 0}, {'wave_width': 20}):
                with patch.object(backend.subprocess, 'run') as execute:
                    failed = plugin.handle_event(Event(row.id, 'activate'), configured(invalid))
                    assert failed.tone == 'error', invalid
                    execute.assert_not_called()
            with patch.object(backend.subprocess, 'run') as execute:
                assert plugin.handle_event(Event(row.id, 'activate'), HostServices(config, cancelled=lambda: True)).tone == 'error'
                execute.assert_not_called()
                execute.side_effect = subprocess.TimeoutExpired(['fake-awww'], 5)
                assert 'may already have changed' in plugin.handle_event(Event(row.id, 'activate'), host).message
            with patch.dict(os.environ, {'WALLPAPER_TEST_EXIT': '1'}):
                assert plugin.handle_event(Event(row.id, 'activate'), host).tone == 'error'
            with patch.object(backend.shutil, 'which', return_value=None):
                assert 'not installed' in plugin.handle_event(Event(row.id, 'activate'), host).message
            first.write_bytes(PNG + b'changed')
            with patch.object(backend.subprocess, 'run') as execute:
                assert 'changed' in plugin.handle_event(Event(row.id, 'activate'), host).message
                execute.assert_not_called()
            refreshed = plugin.handle_event(Event('refresh', 'activate'), host)
            new_row = next(item for item in refreshed.results if item.title == first.name)
            assert new_row.id != row.id
            first.unlink()
            first.symlink_to(outside)
            assert plugin.handle_event(Event(new_row.id, 'activate'), host).tone == 'error'
            filtered = plugin.handle_event(Event('catalog', 'filter', {'value': view.catalog.filters[2]}), host)
            assert [item.title for item in filtered.results] == ['ocean.png']
            plugin.handle_event(Event('catalog', 'filter', {'value': 'All folders'}), host)
            changed_host = HostServices({'plugins': {'hyprland-wallpapers': {'config': {'directories': []}}}})
            assert plugin.handle_event(Event(row.id, 'activate'), changed_host).tone == 'error'
            assert not plugin.search('', changed_host).results
            (folder / 'second.png').write_bytes(PNG)
            roots, _ = backend.directories([str(folder)])
            for limit in ('MAX_IMAGES', 'MAX_ENTRIES'):
                with patch.object(backend, limit, 1):
                    assert 'limit reached' in backend.scan(roots)[1]
            for value in ('[', '{}', '["relative"]', '[null]', '[""]', json.dumps([str(folder)] * 17), '["\\udcff"]'):
                try:
                    backend.directories(value)
                except backend.WallpaperError:
                    pass
                else:
                    raise AssertionError(value)
            assert backend.directories([str(temp / 'missing')])[1]
    print('Wallpaper: typed/legacy folders, passive preview DTOs, filters, all option argv, failures and stale/scope guards passed; fake awww only')


if __name__ == '__main__':
    main()
