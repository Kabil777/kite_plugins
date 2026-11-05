"""Native split wallpaper browser; selection previews and only activation applies."""
from plugin_api import Action, Catalog, MenuAction, Node, Result, Toast, View, plugin_config
from .backend import OPTION_FIELDS, WallpaperError, apply, directories, scan

PLUGIN_ID = 'hyprland-wallpapers'
# ponytail: worker-local metadata index; Ctrl+R rescans. Add watchers only if live updates are needed.
_cache_key = None
_entries = {}
_scan_warning = ''
_folder = None


def _catalog(host, force=False):
    global _cache_key, _entries, _scan_warning
    roots, warnings = directories(plugin_config(host, PLUGIN_ID).get('directories', []))
    if host.cancelled():
        raise WallpaperError('Wallpaper request cancelled')
    if force or roots != _cache_key:
        items, _scan_warning = scan(roots, host.cancelled)
        _entries = {item.id: item for item in items}
        _cache_key = roots
    return roots, ' '.join((*warnings, _scan_warning)).strip()


def _filters(roots):
    return {'All folders': None, **{f'{index + 1}. {root.name}'[:256]: root for index, root in enumerate(roots)}}


def _results(query, host, force=False, toast=None):
    try:
        roots, warning = _catalog(host, force)
        terms = query.casefold().split()
        matches = [item for item in _entries.values()
                   if (_folder is None or item.path.is_relative_to(_folder))
                   and all(term in str(item.path).casefold() for term in terms)]
        results = tuple(Result(item.id, item.path.name, item.path.parent.name,
                               'preferences-desktop-wallpaper', Action('activate', item.id),
                               accessibility_label=('Wallpaper ' + str(item.path))[-512:], keywords=str(item.path),
                               preview=Node('image_preview', item.id + '-image', {'source': str(item.path), 'alt': item.path.name}))
                        for item in matches[:200])
        footer = (f'{len(matches)} matches; refine your search (first 200 shown).' if len(matches) > 200 else
                  '↑/↓ previews · Enter applies · Simple uses Step, not Duration.')
        return View(title='Hyprland Wallpapers', results=results, error=warning[:512], toast=toast,
                    actions=(MenuAction('refresh', 'Refresh wallpapers', Action('activate', 'refresh'), glyph='\uf021', shortcut='Ctrl+R'),),
                    catalog=Catalog(placeholder='Search wallpapers…', heading='Wallpapers', footer=footer,
                                    preserve_order=True, layout='list_detail', filters=tuple(_filters(roots)),
                                    settings_keys=('resize', 'transition_type', 'transition_duration'),
                                    option_keys=tuple(field['key'] for field in OPTION_FIELDS), primary_label='Apply to all displays',
                                    empty='Add folders in Plugin Settings to begin.' if not roots else 'No matching wallpapers.'))
    except WallpaperError as error:
        return View(title='Hyprland Wallpapers', error=str(error)[:512])


def search(query, host):
    return _results(query, host)


def handle_event(event, host):
    global _folder
    query = event.payload.get('query', '')
    if not isinstance(query, str) or len(query) > 4096:
        return Toast('Wallpaper action failed', 'Invalid search context.', 'error')
    try:
        roots, _ = _catalog(host)
        if event.node_id == 'catalog' and event.name == 'filter':
            choices = _filters(roots)
            if event.payload.get('value') not in choices:
                raise WallpaperError('Folder filter expired. Refresh the list.')
            _folder = choices[event.payload['value']]
            return _results(query, host)
        if event.node_id == 'refresh' and event.name == 'activate':
            return _results(query, host, True)
        item = _entries.get(event.node_id)
        if item is None or event.name != 'activate':
            raise WallpaperError('Wallpaper selection expired. Refresh the list.')
        overrides = event.payload.get('settings', {})
        if not isinstance(overrides, dict) or set(overrides) - {field['key'] for field in OPTION_FIELDS}:
            raise WallpaperError('Invalid image options snapshot.')
        options = {**plugin_config(host, PLUGIN_ID), **overrides}
        apply(item, roots, host.cancelled, options)
        return _results(query, host, toast=Toast('Wallpaper applied', 'All default-namespace displays.', 'success'))
    except WallpaperError as error:
        return Toast('Wallpaper action failed', str(error)[:512], 'error')
