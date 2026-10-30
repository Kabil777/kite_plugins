# Passwords

## Install this optional plugin

Already see **Passwords** in KITE? Skip to [Start here](#start-here); do not add a second copy.

Install KITE first and make sure `gopass` works in your terminal. This plugin uses your existing store; it does not create, move or upload one. Extra tool plugins also need a working systemd user session.

KITE does not install this plugin by default. Follow [README.md](README.md) if you need to clone the registry first. Close KITE, then from your persistent **kite_plugins registry checkout root**, link the package:

```sh
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/kite/plugin"
ln -sT -- "$PWD/plugins/gopass" "${XDG_CONFIG_HOME:-$HOME/.config}/kite/plugin/gopass"
```

If the destination already exists, inspect **Plugin marketplace → Installed** instead of overwriting it. Keep the checkout in place while using the link. Reopen KITE and look for **Passwords**; use **Options → Allow in KITE** if needed. An explicit YAML disable still wins.

The [official registry](https://github.com/Kabil777/kite_plugins) will offer marketplace installation when a reviewed release is published. A local source link is not a manager-owned package and is not uninstalled by marketplace actions.

## Start here

Passwords uses your existing **gopass** password store. It does not create or move a store for you.

1. Make sure gopass works in your terminal: `gopass ls` should list your entries.
2. Open KITE, search for **Passwords**, and press Enter.
3. Choose a Vault, then choose an account.

A **Vault** is the first folder in an existing entry path. For example, `example.com/alice` appears as account **alice** inside **example.com**. This is only a label in KITE; the stored path is unchanged. Entries without a folder appear in the first list.

If you do not have a gopass store yet, follow the setup instructions at https://www.gopass.pw/ before using Passwords.

## Copy a password

1. Open a Vault and select an account.
2. Press Enter to unlock that entry. Finish any GPG/age prompt that appears.
3. Choose **Copy password** and press Enter.
4. Paste into the application that needs it.

Browsing never unlocks or copies a password. Unlocking reveals only the copy choices; the password itself stays hidden. **Copy path** copies the entry's name, not its password.

**Copy password** uses the normal system clipboard for **Ctrl+V**, not KITE's search buffer or the middle-click PRIMARY selection. A separate clipboard-history manager may keep copied values, and KITE does not automatically clear them. To test your own desktop, use a disposable entry containing only dummy text and paste that value into an editor. Never paste a real password into a terminal, issue report or diagnostic command.

## Go back

Escape returns one screen at a time:

**Copy choices → Accounts → Vaults → KITE → Close**

Your previous search and selected row are restored. There are no Back rows mixed into accounts or copy choices. Returning to a list does not unlock entries again.

## Find an account

Type to filter Vault names and account names. Opening a Vault puts its prefix, such as `example.com/`, in the search field. Type after that prefix to narrow its accounts.

Use Escape to leave the Vault rather than deleting its name from every search.

## Create a password

1. Inside Passwords, press **Alt+I**, or choose **Actions → Create Password**.
2. Enter a path such as `example.com/alice`. If you opened a Vault first, its prefix is already filled in.
3. Enter the password in the masked field.
4. Choose **Save password**, or press Enter in a field.

The form uses the full content area. Header and bottom bar stay visible. Existing entries are never overwritten; choose another path if an entry already exists.

Cancel with **Cancel**, **Escape**, or **Ctrl+G**. If you edited the form, KITE asks whether to discard changes or keep editing. Escape on that question keeps editing.

If saving fails, correct the reported problem and re-enter the password. The entry path stays filled in, but the password field is cleared for safety.

## Sync with your Git remote

Inside Passwords, press **Ctrl+S**, or choose **Actions → Sync passwords**. Sync never runs while you browse or search.

- With a configured remote, gopass performs its normal sync. Finish any SSH/key prompt if requested.
- Without a remote, KITE keeps your list on screen and shows an error notification. Click **×** to dismiss it.
- Sync is not offered in the creation form. Finish or cancel the form first.

### Set up a remote

Open a **regular terminal**—for example Kitty, Konsole or GNOME Terminal. Do **not** enter these commands into KITE's search field, its password form or a Python prompt. You can run them from any folder: `gopass` locates its configured store.

Check the default store's remote:

```sh
gopass git remote -v
```

If `origin` already points to your intended private repository, leave it alone. If there is no `origin`, create/use a **separate private password-store repository**, replace the quoted placeholder below with its real Git URL, then run:

```sh
gopass git remote add origin 'YOUR_PRIVATE_STORE_GIT_URL'
```

Do not use KITE's application or plugin-registry repository as your password store. Those repositories are public and unrelated to your encrypted entries.

If Passwords is configured for a mounted store alias such as `work`, use that same alias in the terminal instead:

```sh
gopass git --store work remote -v
# Only if that store has no origin; replace the placeholder first:
gopass git --store work remote add origin 'YOUR_PRIVATE_STORE_GIT_URL'
```

`work` is an example existing alias, not a new store. Omit `--store` for the default store. Check `gopass git --help` if your installed version uses different options. These commands inspect/configure the Git remote; they do not copy any password.

Return to Passwords and retry **Ctrl+S**. KITE does not choose a repository, store your Git credentials, or configure remotes automatically. Git receives encrypted entries, but repository names and file paths can still reveal metadata; use a private repository.

## Shortcuts

| Action | Shortcut |
| --- | --- |
| Open Actions | Ctrl+K |
| Open or close this guide | Ctrl+? |
| Create password, while browsing | Alt+I |
| Sync passwords, while browsing | Ctrl+S |
| Cancel creation | Ctrl+G or Escape |
| Return to the previous screen | Escape |

On a US keyboard, Ctrl+? means Ctrl+Shift+/. The symbols ⌃, ⌥ and ↩ mean Ctrl, Alt and Enter.

Create, Sync and Cancel bindings work only inside Passwords and only where their actions are available. They never become desktop-global shortcuts. While a call is running, ordinary action shortcuts are disabled to avoid duplicate operations; back/cancel remains available.

## Common problems

**“gopass executable not found”** — install gopass and make sure your desktop session can find it in PATH.

**Unlocking times out or fails** — check that gopass can unlock the same entry in your terminal, and that its GPG/age key and pinentry are available. Do not paste your password or private key into KITE's search field.

**“No Git remote configured”** — follow Set up a remote above. Dismissing the notification does not retry sync.

**Sync reports a command failure or timeout** — this is not the same as having no remote. Check gopass and your Git/SSH setup in your own terminal. KITE's local fixture checks do not authenticate to GitHub or verify your repository permissions. A failed/cancelled sync may have partly completed; inspect your store before retrying.

**Wrong store** — Passwords uses the default gopass store unless its KITE configuration selects a mounted store. Ask your setup maintainer to check `plugins.gopass.config.store` in `~/.config/kite/config.yaml`.

**An operation was cancelled** — KITE requests cancellation, but an operation already committed may have completed. Check your store before retrying a creation; KITE will refuse an overwrite.
