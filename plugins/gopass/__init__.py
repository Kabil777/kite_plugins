"""Vault-first password browser. Vault labels never change underlying entry paths."""
from dataclasses import replace
from hashlib import sha256
import re
from plugin_api import Action, Catalog, Event, MenuAction, Node, Result, Toast, View, plugin_config
from .backend import BackendError, create_entry, entries, password, sync


def _store(host):
    return plugin_config(host, 'gopass').get('store') or host.config.get('gopass', {}).get('store', '')


def _id(kind, value):
    return kind + ':' + sha256(value.encode()).hexdigest()


# ponytail: small offline name rules; unknown names keep native vault/password defaults.
_ICON_RULES = (
    ({'github'}, 'web-browser', '\uf09b'),
    ({'gitlab'}, 'web-browser', '\uf296'),
    ({'bitbucket'}, 'web-browser', '\uf171'),
    ({'google'}, 'web-browser', '\uf1a0'),
    ({'amazon', 'aws'}, 'network-server', '\uf270'),
    ({'microsoft', 'windows', 'azure'}, 'computer', '\uf17a'),
    ({'apple', 'icloud'}, 'computer', '\uf179'),
    ({'linux'}, 'computer', '\uf17c'),
    ({'slack'}, 'internet-chat', '\uf198'),
    ({'telegram'}, 'internet-chat', '\uf1d8'),
    ({'reddit'}, 'web-browser', '\uf1a1'),
    ({'spotify'}, 'multimedia-player', '\uf1bc'),
    ({'steam'}, 'applications-games', '\uf1b6'),
    ({'dropbox'}, 'folder-remote', '\uf16b'),
    ({'email', 'mail', 'gmail', 'outlook', 'protonmail'}, 'mail-unread', '\uf0e0'),
    ({'ssh', 'terminal'}, 'utilities-terminal', '\uf120'),
    ({'server', 'servers', 'hosting'}, 'network-server', '\uf233'),
    ({'wifi', 'wireless'}, 'network-wireless', '\uf1eb'),
    ({'bank', 'banking', 'finance'}, 'x-office-spreadsheet', '\uf19c'),
    ({'work', 'office'}, 'folder-documents', '\uf0b1'),
    ({'personal', 'family'}, 'avatar-default', '\uf007'),
    ({'admin', 'administrator'}, 'security-high', '\uf132'),
    ({'backup', 'recovery'}, 'document-revert', '\uf1cd'),
)


def _name_icon(name, vault=False):
    # Prefer a matching entry name, then inherit its vault/service context. Never fetch favicons.
    for part in reversed(name.casefold().split('/')):
        words = set(re.findall(r'[a-z0-9]+', part))
        for aliases, icon, glyph in _ICON_RULES:
            if words & aliases:
                return icon, glyph
    if '.' in name:
        return 'web-browser', '\uf0ac'
    return ('folder', '\uf187') if vault else ('dialog-password', '\uf084')


def _catalog(domain='', message=''):
    return Catalog(placeholder='Search vaults or passwords…',
                   footer=(message or (f'{domain} · Select a password · Esc back' if domain else 'Select a vault · Esc back'))[:256],
                   heading=(domain or 'Vaults')[:256], empty='No matching passwords', preserve_order=True)


def _menu_actions(host):
    actions = [MenuAction('create', 'Create Password', Action('activate', 'create', push=True),
                          glyph='+', shortcut='Alt+I')]
    store = _store(host)
    title = 'Sync passwords' if store else 'Sync passwords (all stores)'
    actions.append(MenuAction('sync', title, Action('activate', 'sync'), glyph='\uf021', shortcut='Ctrl+S'))
    return tuple(actions)


def _results(query, host, message='', error=''):
    store = _store(host)
    try:
        paths = entries(store, host.cancelled)
        groups, roots = {}, []
        for path in paths:
            domain, slash, _ = path.partition('/')
            if slash:
                groups.setdefault(domain, []).append(path)
            else:
                roots.append(path)
        folder, slash, term = query.partition('/')
        domain = next((name for name in groups if slash and name.casefold() == folder.casefold()), '')
        rows = []
        if domain:
            matches = [path for path in groups[domain] if term.casefold() in path.split('/', 1)[1].casefold()]
        else:
            needle = query.casefold()
            for name in sorted(groups, key=str.casefold):
                if needle in name.casefold() or any(needle in path.casefold() for path in groups[name]):
                    icon, glyph = _name_icon(name, vault=True)
                    rows.append(Result(_id('domain', name), name, f'{len(groups[name])} passwords', icon,
                                       Action('query', name + '/', push=True), glyph=glyph, tag='Vault',
                                       keywords=name + ' ' + query))
            matches = [path for path in roots if needle in path.casefold()]
        for path in matches[:100]:
            icon, glyph = _name_icon(path)
            rows.append(Result(_id('entry', path), path.split('/', 1)[1] if domain else path,
                               'Enter to unlock', icon, Action('activate', path, push=True),
                               glyph=glyph, keywords=path, tag=domain[:256]))
        return View(title='Passwords', results=tuple(rows[:200]), catalog=_catalog(domain, message),
                    error=error, actions=_menu_actions(host))
    except (BackendError, ValueError) as error:
        return View(title='Passwords', error=str(error))


def search(query, host):
    return _results(query, host)


def _create_form(entry='', message=''):
    form = Node('form', 'create-form', {
        'title': 'Create password',
        'description': 'Save an encrypted entry. Existing entries are never overwritten.',
        'error': message,
        'submit_text': 'Save password',
    }, children=(
        Node('label', 'entry-label', {'text': 'Vault / entry path'}),
        Node('text_input', 'entry', {'text': entry, 'placeholder': 'example.com/account'}),
        Node('label', 'password-label', {'text': 'Password'}),
        Node('text_input', 'password', {'placeholder': 'Password', 'password': True}),
    ), events={'submit': {}})
    return View(title='Passwords', nodes=(form,),
                actions=(MenuAction('cancel', 'Cancel creation', Action('back', ''), shortcut='Ctrl+G'),))


def handle_event(event: Event, host):
    store = _store(host)
    query = event.payload.get('query', '')
    if event.node_id == 'create' and event.name == 'activate':
        domain = query.split('/', 1)[0] + '/' if '/' in query else ''
        return _create_form(domain)
    if (event.node_id == 'create-form' and event.name == 'submit') or (event.node_id == 'save' and event.name == 'activate'):
        values = event.payload.get('inputs', {})
        entry, secret = values.get('entry', ''), values.get('password', '')
        try:
            create_entry(entry, secret, store, host.cancelled)
        except (BackendError, ValueError) as error:
            return _create_form(entry, str(error))
        return _results(query, host, 'Password entry created')
    if event.node_id == 'sync' and event.name == 'activate':
        try:
            sync(store, host.cancelled)
        except (BackendError, ValueError) as error:
            return Toast('Could not sync passwords', str(error) + ' Open How to for setup steps.', 'error')
        return replace(_results(query, host, 'Sync complete'), toast=Toast('Passwords synced', tone='success'))
    if event.name == 'activate' and event.node_id.startswith('entry:'):
        entry = event.payload.get('value', event.node_id)
        try:
            secret = password(entry, store, host.cancelled)
        except (BackendError, ValueError) as error:
            return _results(query, host, error=str(error))
        domain = entry.split('/', 1)[0] if '/' in entry else ''
        return View(title='Passwords', catalog=_catalog(entry, 'Choose a copy action · Esc back'),
                    actions=_menu_actions(host), results=(
            Result('copy-password', 'Copy password', 'Password stays hidden', 'edit-copy',
                   Action('copy', secret), glyph='\uf0c5', keywords=query, tag=domain[:256]),
            Result('copy-path', 'Copy path', 'Entry path without store alias', 'edit-copy', Action('copy', entry),
                   glyph='\uf0c5', keywords=query, tag=domain[:256]),
        ))
    return View(error='Unknown password action')
