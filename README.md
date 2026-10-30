# KITE plugin registry

Find extra tools for [KITE](https://github.com/Kabil777/kite), the Linux launcher.

This repository holds optional plugin source packages, their individual guides, and KITE's marketplace catalog. **Cloning this repository does not install or activate any plugin.** Password stores, private settings, credentials and installed runtime data do not belong here.

## Plugins

| Plugin | What it adds | Requirements | Install and use |
| --- | --- | --- | --- |
| **Passwords (Gopass)** · `gopass` | Browse an existing store, explicitly copy/create entries, and manually sync | Configured `gopass`, KITE, systemd user services and cgroup v2 | [Plugin README](plugins/gopass/README.md) · [User guide](plugins/gopass/HOWTO.md) |

Every directory under `plugins/` has its own README with setup, requirements and usage. Gopass is **not bundled with or installed by KITE's default installer**; follow its README only if you want it.

**Marketplace status:** `index.json` is currently empty. Source installation of Gopass is available through its guide, but there are no published marketplace packages yet. Entries will be added only after a real release archive has been published and reviewed. Core protocol/search examples remain in [KITE's examples](https://github.com/Kabil777/kite/tree/main/examples).

## Add this registry to KITE

Install KITE first using its [getting-started guide](https://github.com/Kabil777/kite#setup-with-uv).

Then:

1. Open KITE and search for **Plugin marketplace**.
2. Choose **Configure** from the dropdown at the top.
3. Paste this catalog address and choose **Save source**:

   ```text
   https://raw.githubusercontent.com/Kabil777/kite_plugins/main/index.json
   ```

4. Choose **Browse** to refresh the list. An empty list is expected while the catalog has no releases.
5. When packages are available, select one, read its requirements and source, and approve installation only if you trust it.

Prefer a terminal? Close KITE before changing its source:

```sh
~/.local/bin/kite plugins source https://raw.githubusercontent.com/Kabil777/kite_plugins/main/index.json
~/.local/bin/kite plugins search
```

No GitHub account or SSH key is needed to browse this public catalog.

## Install, allow and open are different steps

- **Install** downloads the exact reviewed archive and checks its SHA-256 checksum. It does not run the plugin.
- **Allow in KITE** permits activation. A YAML `enabled: false` still takes precedence.
- **Open** starts a tool plugin. A selected ranking plugin starts when root search needs it.

KITE does not install a plugin's system dependencies for you. Follow the package's guide. A checksum confirms which bytes you received; it does not make code safe. Plugins retain your user's file and network access.

## If something looks wrong

- **Browse is empty:** that is currently normal; check the status above.
- **A plugin is installed but unavailable:** open **Installed → Options**, check its requirements and **Allow in KITE**, then check for a YAML disable.
- **The network is unavailable:** KITE may show a clearly labeled cached catalog. Installing still needs the release archive.
- **Cleanup or ownership needs attention:** use KITE's **Check cleanup / recover** flow. Do not delete registry files or replace managed links to bypass the warning.

For everyday help, read the [KITE user guide](https://github.com/Kabil777/kite/blob/main/docs/howto.md).

## Publish a plugin

Start with [Contributing](CONTRIBUTING.md). It explains how to prepare a release, calculate its checksum and submit a catalog entry.

For the exact fields and archive rules, see KITE's [catalog reference](https://github.com/Kabil777/kite/blob/main/catalog/README.md#schema-v1). For backend authors, see the [plugin protocol](https://github.com/Kabil777/kite/blob/main/docs/plugin-protocol.md).

## Repositories

- [KITE application, source and examples](https://github.com/Kabil777/kite)
- [This registry's catalog](index.json)
- [Report a registry problem](https://github.com/Kabil777/kite_plugins/issues)
