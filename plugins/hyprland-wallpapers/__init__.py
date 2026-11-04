"""Search, preview and explicitly apply configured wallpapers using KITE's shared UI."""
from plugin_api import Action, Catalog, MenuAction, Node, Result, Toast, View, plugin_config
from .backend import WallpaperError, apply, directories, scan, validate

PLUGIN_ID = 'hyprland-wallpapers'
# ponytail: worker-local metadata index; Ctrl+R rescans. Add watchers only if live updates are needed.
_cache_key = None
_entries = {}
_scan_warning = ''


def _catalog(host, force=False):
    global _cache_key, _entries, _scan_warning
    roots, warnings = directories(plugin_config(host, PLUGIN_ID).get('directories', '[]'))
    if host.cancelled():
        raise WallpaperError('Wallpaper request cancelled')
    if force or roots != _cache_key:
        items, _scan_warning = scan(roots, host.cancelled)
        _entries = {item.id: item for item in items}
        _cache_key = roots
    warning = ' '.join((*warnings, _scan_warning)).strip()
    return roots, warning


def _actions():
    return (MenuAction('refresh', 'Refresh wallpapers', Action('activate', 'refresh'),
                       glyph='\uf021', shortcut='Ctrl+R'),)


def _results(query, host, force=False, toast=None):
    try:
        roots, warning = _catalog(host, force)
        terms = query.casefold().split()
        matches = [item for item in _entries.values()
                   if all(term in str(item.path).casefold() for term in terms)]
        results = tuple(Result(item.id, item.path.name, str(item.path.parent)[-2048:],
                               'preferences-desktop-wallpaper', Action('activate', item.id, push=True),
                               accessibility_label=('Preview ' + str(item.path))[-512:], keywords=str(item.path))
                        for item in matches[:200])
        footer = (f'{len(matches)} matching wallpapers; first 200 shown. Refine your search.' if len(matches) > 200 else
                  f'{len(matches)} wallpapers. Enter to preview; Ctrl+R refreshes.')
        return View(title='Hyprland Wallpapers', results=results, error=warning[:512], actions=_actions(), toast=toast,
                    catalog=Catalog(placeholder='Search wallpaper filenames and folders…', heading='Wallpapers',
                                    footer=footer[:256], preserve_order=True,
                                    empty='Add folders in Plugin marketplace → Installed → Options → Settings.' if not roots else
                                          'No matching wallpapers. Check folders or press Ctrl+R to refresh.'))
    except WallpaperError as error:
        return View(title='Hyprland Wallpapers', error=str(error)[:512], actions=_actions())


def search(query, host):
    return _results(query, host)


def handle_event(event, host):
    query = event.payload.get('query', '')
    if not isinstance(query, str) or len(query) > 4096:
        return Toast('Could not change wallpaper', 'Invalid wallpaper search context.', 'error')
    if event.node_id == 'refresh' and event.name == 'activate':
        return _results(query, host, True)
    try:
        roots, _ = _catalog(host)
        applying = event.node_id.startswith('apply:') and event.name == 'submit'
        identifier = event.node_id.removeprefix('apply:') if applying else event.node_id
        item = _entries.get(identifier)
        if item is None or not applying and event.name != 'activate':
            raise WallpaperError('Wallpaper selection expired. Return to the list and refresh it.')
        if applying:
            apply(item, roots, host.cancelled)
            return _results(query, host,
                            toast=Toast('Wallpaper applied', 'All displays in the default awww daemon namespace.', 'success'))
        path = validate(item, roots)
        preview = Node('form', 'apply:' + item.id, {
            'title': 'Wallpaper preview', 'description': item.path.name[:256], 'submit_text': 'Apply to all displays',
        }, children=(Node('image_preview', 'wallpaper-preview', {'source': str(path), 'alt': item.path.name[:512]}),
                     Node('label', 'wallpaper-target', {'text': 'All displays. Existing awww transitions are used.', 'wrap': True})),
                     events={'submit': {}})
        return View(title='Hyprland Wallpapers', nodes=(preview,),
                    actions=(MenuAction('back', 'Back to wallpapers', Action('back', '')),))
    except WallpaperError as error:
        return Toast('Could not change wallpaper', str(error)[:512], 'error')
