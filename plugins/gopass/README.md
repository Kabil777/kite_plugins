# Passwords for KITE — Gopass

Use your existing [gopass](https://www.gopass.pw/) store from KITE: browse entry names, explicitly unlock and copy a password, create an entry, or manually sync with your own Git remote.

**This is optional. KITE does not bundle or install this plugin by default.** Cloning the registry alone does not install it either. There is no published marketplace release yet; the instructions below are an explicit source install.

Already using Passwords? Go to the [user guide](HOWTO.md). Do not add another copy.

## Before you start

You need:

- [KITE installed](https://github.com/Kabil777/kite#setup-with-uv).
- `gopass` installed and a store already configured. Confirm it works in your own terminal before using this plugin.
- A working systemd user session and cgroup v2 for KITE's tool-plugin workers.
- Your usual GPG/age unlock setup, and a working KITE clipboard backend such as `wl-clipboard` on Wayland or `xclip` on X11.

The plugin does not create a password store, move its files, configure a remote or install dependencies for you. Keep your store, keys and personal settings outside this repository.

## Install only if you want it

Close KITE. Keep a persistent checkout of `kite_plugins`; if you do not have one yet:

```sh
mkdir -p "$HOME/Projects"
git clone https://github.com/Kabil777/kite_plugins.git "$HOME/Projects/kite_plugins"
```

From the registry checkout root, link this package:

```sh
cd "$HOME/Projects/kite_plugins"
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/kite/plugin"
ln -sT -- "$PWD/plugins/gopass" "${XDG_CONFIG_HOME:-$HOME/.config}/kite/plugin/gopass"
```

If you chose a different checkout location, use it in the `cd` command. Keep that folder in place while using the link. If Passwords is already installed or the destination exists, stop and inspect **Plugin marketplace → Installed** instead of forcing replacement. Do not mix a local source link with a separate marketplace package of the same ID.

Reopen KITE and search for **Passwords**. In Installed → Options, choose **Allow in KITE** if necessary. An explicit YAML disable still prevents activation. Installing/linking does not unlock, copy or sync anything; the worker starts only when you open the tool.

## First use

1. Open KITE, search **Passwords**, and press Enter.
2. Choose a Vault, then an account. Vaults are labels for existing folders; stored paths do not change.
3. Press Enter to unlock that entry and complete your usual key prompt.
4. Choose **Copy password**, then paste into the application that needs it.

Browsing lists names only. Copying is a separate explicit action. **Copy path** copies the entry name, not its password. Do not type a password into KITE's main search.

For creation, sync, keyboard shortcuts and troubleshooting, read [HOWTO.md](HOWTO.md). KITE shows the same guide with **Ctrl+?** inside Passwords.

## Choose a mounted store (optional)

Leave the setting empty for gopass's normal default store. For an existing mounted alias such as `work`, use **Installed → Options → Settings**, or merge this into your KITE YAML:

```yaml
plugins:
  gopass:
    enabled: true
    config:
      store: work
```

This does not install the plugin or create a store. Restart KITE after manual YAML changes. Legacy `gopass.store` remains supported for existing configurations.

## Disable, update or remove

- **Disable:** choose **Disallow in KITE**. Your store is not changed.
- **Update a source install:** close KITE, review/pull changes in this checkout, then reopen KITE. Do not edit a second copy in the installation directory.
- **Remove a source install:** close KITE and remove only the authored link you created, after confirming it points to this checkout. Marketplace uninstall does not own this local link.
- **Managed package:** use marketplace update/uninstall for a manager-owned package; never replace its link by hand.

None of these actions should delete your Gopass store, keys or Git repository.

## Safety and verification

Plugins retain your user's privileges: review the code before enabling it. Password creation uses stdin, refuses overwrites and does not put values in command-line arguments. Decrypted values are not rendered as previews or saved in navigation history. Cancelling a request cannot undo an operation that already completed.

Developers can run fixture-only checks from a sibling KITE checkout with its uv environment prepared:

```sh
uv run --locked --no-sync python ../kite_plugins/plugins/gopass/backend.py
uv run --locked --no-sync python -m tests.check_gopass_sync
```

The backend check mocks its commands. The sync check uses a fake Gopass executable and temporary local Git repositories, not real credentials, password entries, GitHub or a live store. Set `KITE_GOPASS_SOURCE` if the package is not in the default sibling checkout.

For KITE integration details, see its [plugin guide](https://github.com/Kabil777/kite/blob/main/docs/plugins.md) and [frontend reference](https://github.com/Kabil777/kite/blob/main/docs/frontend.md).
