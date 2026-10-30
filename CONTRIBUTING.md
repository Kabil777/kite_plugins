# Share a plugin with KITE users

Thank you for contributing. This repository keeps optional plugin packages and a reviewed catalog of downloadable releases. It is not a place for your personal configuration, secret stores or build caches.

## Add or update plugin source

Use `plugins/<plugin-id>/` for each maintained package. Every plugin directory **must have its own README.md** explaining what it does, prerequisites, explicit installation, first use and removal. Include an actionable `HOWTO.md` for KITE's in-app help, keep manifest/backend files together, and add or update its row in the main [plugin list](README.md#plugins).

Source-only packages may be listed there before a release exists. Mark that status clearly and **do not add a fake installable entry to index.json**. Adding source or cloning this repository must never install, enable or open a plugin automatically. Source may live here or in an author's public repository; preserve its licensing and provenance.

## Before you submit a marketplace release

You need:

- A public GitHub repository containing your plugin source (this repository for packages maintained here).
- A working API-v2 package with a `plugin.json` manifest.
- A short `HOWTO.md` explaining what the plugin does, what users must install, and how to get started.
- A versioned ZIP uploaded as a **GitHub Release asset**, plus its actual SHA-256 checksum.
- Permission to distribute every included file and its required license notices.

If you are still writing the plugin, start with [KITE's plugin guide](https://github.com/Kabil777/kite/blob/main/docs/plugins.md). Executable backends can use any language; see the [shared protocol](https://github.com/Kabil777/kite/blob/main/docs/plugin-protocol.md).

## 1. Prepare a clean package

The archive must contain one top-level directory named after the manifest ID:

```text
my-plugin/
  plugin.json
  README.md
  HOWTO.md
  ...the backend files needed to run it
```

Python packages need their `__init__.py` entry. Executable packages declare `command` and include the necessary backend files. Preserve executable permissions for native binaries.

Do not include `.venv`, build caches, personal configuration, password stores, keys, tokens, logs or your entire development checkout. Include all required third-party notices. Native packages should explain their supported OS/architecture and any runtime libraries; KITE does not choose an architecture-specific asset automatically.

Read the [archive rules](https://github.com/Kabil777/kite/blob/main/catalog/README.md#build-a-release-asset) before packaging. KITE rejects unsafe paths, links, special files and conflicting archive entries.

## 2. Publish the ZIP

Create a stable version such as `1.0.0` in your source repository, upload the reviewed ZIP to its GitHub Release, and calculate the checksum:

```sh
sha256sum my-plugin-1.0.0.zip
```

Verify that the uploaded asset has those same bytes. Do not replace an existing version's archive with different contents; publish a new version instead.

Use a Release asset URL, not GitHub's automatically generated source archive. We cannot merge an entry that points to a planned release, placeholder URL or invented hash.

## 3. Add a catalog entry

Fork this repository, create a branch, and edit `index.json`.

Keep its top-level shape as `{"schema":1,"plugins":[...]}`. Each entry needs its ID, name, short summary, author, public source repository, explicit latest version and release records. Declare external commands and manual setup requirements where needed.

The exact field definitions and a clearly marked template are in the [catalog format reference](https://github.com/Kabil777/kite/blob/main/catalog/README.md#schema-v1). Copy the structure, then use your real published metadata. Never commit the placeholders as an installable entry.

Check JSON syntax locally:

```sh
python3 -m json.tool index.json > /dev/null
```

For full schema validation, keep KITE and this registry in sibling directories. From the KITE checkout, after setting up its uv environment, run:

```sh
uv run --locked --no-sync python - <<'PY'
from pathlib import Path
from main.plugin_manager import _read_json, validate_catalog

validate_catalog(_read_json(Path('../kite_plugins/index.json'), 2 * 1024 * 1024))
print('Catalog is valid')
PY
```

Validation does not run a plugin. It also does not replace source review or testing the package yourself in an appropriate environment.

## 4. Open a pull request

Include:

- What the plugin does and who it helps.
- Its source repository and exact Release asset URL.
- The archive's checksum and a brief test summary.
- Required binaries/libraries, supported platforms and license details.
- Any access to files, network services or secret stores that users should understand.

Maintainers review the source, guide, archive contents, compatibility and checksum before adding an entry. There is no automatic approval, dependency installation or execution hook.

## Maintainer checklist

- Confirm the source and asset are publicly accessible and belong to the declared repository.
- Check manifest ID/name/API and package-directory identity.
- Inspect the actual archive; verify the downloaded bytes against the recorded hash.
- Read the user guide, dependency instructions and license notices.
- Preserve existing release records unless there is a clear reason not to; select `latest` explicitly.
- Validate the catalog with KITE's validator and review the diff before merging.

To remove or flag a problematic entry, open an issue or pull request describing the problem. Changing this catalog does not automatically remove code from users' computers; users control updates, disablement and uninstalling through KITE.
