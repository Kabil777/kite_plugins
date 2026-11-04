"""Run from kite_plugins with PYTHONPATH=../kite and KITE's uv environment. No real daemon is contacted."""
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
        environment = {'HOME': str(temp), 'PATH': str(binary), 'QT_QPA_PLATFORM': 'offscreen',
                       'WALLPAPER_TEST_LOG': str(log)}
        for name in ('CONFIG', 'CACHE', 'DATA', 'RUNTIME'):
            path = temp / name.lower()
            path.mkdir(mode=0o700)
            environment['XDG_' + name + ('_DIR' if name == 'RUNTIME' else '_HOME')] = str(path)
        with patch.dict(os.environ, environment):
            from main.plugin_api import Event, HostServices, _load_plugin, validate_toast, validate_view
            loaded = _load_plugin(SOURCE)
            assert loaded is not None
            manifest, plugin = loaded
            backend = sys.modules[plugin.__name__ + '.backend']
            assert manifest['configuration'][0]['key'] == 'directories'
            folder = temp / 'images with spaces; not a shell'
            nested = folder / 'nested'
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
            assert len(view.results) == 2 and 'skipped' in view.error
            assert len(plugin.search('ocean', host).results) == 1
            assert len(plugin.search('nested ocean', host).results) == 1
            assert not log.exists(), 'Search must not execute the backend'
            row = next(row for row in view.results if row.title == first.name)
            preview = plugin.handle_event(Event(row.id, 'activate', {'value': str(outside)}), host)
            validate_view(preview)
            form = preview.nodes[0]
            assert form.type == 'form' and form.children[0].props['source'] == str(first)
            assert form.props['submit_text'] == 'Apply to all displays' and not log.exists()
            for event in (Event('apply:unknown', 'submit'), Event(form.id, 'activate'),
                          Event(form.id, 'submit', {'query': []})):
                failed = plugin.handle_event(event, host)
                validate_toast(failed)
                assert failed.tone == 'error' and not log.exists()
            result = plugin.handle_event(Event(form.id, 'submit', {'query': 'forest'}), host)
            validate_view(result)
            assert result.toast.tone == 'success'
            requests = [json.loads(line) for line in log.read_text().splitlines()]
            assert requests == [['img', '--', str(first)]], requests
            assert not (temp / 'unwanted.PNG').exists()
            cancelled = HostServices(config, cancelled=lambda: True)
            with patch.object(backend.subprocess, 'run') as execute:
                failed = plugin.handle_event(Event(form.id, 'submit'), cancelled)
                assert failed.tone == 'error'
                execute.assert_not_called()
                execute.side_effect = subprocess.TimeoutExpired(['fake-awww'], 5)
                failed = plugin.handle_event(Event(form.id, 'submit'), host)
                assert failed.tone == 'error' and 'may already have changed' in failed.message
            with patch.dict(os.environ, {'WALLPAPER_TEST_EXIT': '1'}):
                failed = plugin.handle_event(Event(form.id, 'submit'), host)
                assert failed.tone == 'error' and 'awww-daemon' in failed.message
            with patch.object(backend.shutil, 'which', return_value=None):
                failed = plugin.handle_event(Event(form.id, 'submit'), host)
                assert failed.tone == 'error' and 'not installed' in failed.message
            first.write_bytes(PNG + b'changed')
            with patch.object(backend.subprocess, 'run') as execute:
                failed = plugin.handle_event(Event(form.id, 'submit'), host)
                assert failed.tone == 'error' and 'changed' in failed.message
                execute.assert_not_called()
            refreshed = plugin.handle_event(Event('refresh', 'activate'), host)
            validate_view(refreshed)
            new_row = next(row for row in refreshed.results if row.title == first.name)
            assert new_row.id != row.id
            first.unlink()
            first.symlink_to(outside)
            with patch.object(backend.subprocess, 'run') as execute:
                failed = plugin.handle_event(Event('apply:' + new_row.id, 'submit'), host)
                assert failed.tone == 'error'
                execute.assert_not_called()
            changed_host = HostServices({'plugins': {'hyprland-wallpapers': {'config': {'directories': '[]'}}}})
            assert plugin.handle_event(Event(form.id, 'submit'), changed_host).tone == 'error'
            assert not plugin.search('', changed_host).results
            (folder / 'second.png').write_bytes(PNG)
            roots, _ = backend.directories(json.dumps([str(folder)]))
            for limit in ('MAX_IMAGES', 'MAX_ENTRIES'):
                with patch.object(backend, limit, 1):
                    _, warning = backend.scan(roots)
                    assert 'limit reached' in warning
            for value in ('[', '{}', '["relative"]', '[null]', '[""]', 'x' * 1025, json.dumps([str(folder)] * 17), '["\\udcff"]'):
                try:
                    backend.directories(value)
                except backend.WallpaperError:
                    pass
                else:
                    raise AssertionError(value)
            unavailable, warnings = backend.directories(json.dumps([str(temp / 'missing')]))
            assert not unavailable and warnings
            # Exercise the actual shared Qt form, image decoder and submit dispatch using only the fixture PNG.
            from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
            from main.core import load_config
            from main.frontend import input_values, render_nodes
            from main.frontend.form import Form
            from main.frontend.image_preview import ImagePreview
            app = QApplication.instance() or QApplication([])
            first.unlink()
            first.write_bytes(PNG)
            refreshed = plugin.handle_event(Event('refresh', 'activate'), host)
            row = next(row for row in refreshed.results if row.title == first.name)
            preview = plugin.handle_event(Event(row.id, 'activate'), host)
            widget = QWidget()
            events = []
            render_nodes(QVBoxLayout(widget), preview.nodes, events.append, load_config(temp / 'config.yaml'))
            widget.resize(700, 500)
            widget.show()
            app.processEvents()
            image = widget.findChild(ImagePreview)
            assert image is not None and not image._source.isNull(), 'Native preview must decode the fixture image'
            form_widget = widget.findChild(Form)
            assert form_widget is not None and form_widget.submit_button.isEnabled()
            form_widget.submit_button.click()
            assert events[-1].node_id == preview.nodes[0].id and events[-1].name == 'submit'
            widget.close()
            # The real marketplace builds the JSON directory field from the manifest, without plugin-specific UI.
            from types import SimpleNamespace
            from main.plugin_manager_ui import Marketplace
            class SettingsHost(QWidget):
                def __init__(self):
                    super().__init__()
                    self.cfg = load_config(temp / 'config.yaml')
                    self.cfg.update(config)
                    self.config_path = temp / 'config.yaml'
                    self.package_lease = object()
                    self.plugin_detail_panel = QWidget(self)
                    self.plugin_detail_layout = QVBoxLayout(self.plugin_detail_panel)
                def selected_result(self):
                    return SimpleNamespace(kind='marketplace_item', value=manifest['id'])
                def active_form(self):
                    return self.plugin_detail_panel.findChild(Form)
                def plugin_event(self, identifier, event):
                    events.append(event)
            settings_host = SettingsHost()
            marketplace = Marketplace(settings_host)
            marketplace.page = 'plugin_config'
            marketplace.target = manifest
            marketplace.rows = {manifest['id']: manifest}
            marketplace.config_fields = manifest['configuration']
            marketplace.show_details()
            field_values = input_values(settings_host.plugin_detail_panel)
            assert field_values['config-directories'] == config['plugins'][manifest['id']]['config']['directories']
            assert backend.directories(field_values['config-directories'])[0] == roots + (nested,)
            marketplace.pool.shutdown(wait=True)
            settings_host.close()
    print('wallpaper plugin: PASS (fake awww only; no live wallpaper or daemon changes)')


if __name__ == '__main__':
    main()
