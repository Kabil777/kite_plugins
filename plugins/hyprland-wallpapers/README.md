# Hyprland Wallpapers for KITE

Search wallpaper folders, preview an image, then **Apply to all displays** using [awww](https://codeberg.org/LGFae/awww). Uses KITE's normal search, image preview and Settings form—no extra window or Python dependencies.

**Optional source plugin.** KITE does not install it by default. There is no marketplace archive yet.

## Requirements

- [KITE](https://github.com/Kabil777/kite), with its normal systemd user session and cgroup v2 tool-worker support.
- Hyprland/Wayland and `awww` installed; `awww-daemon` already running in the same session, in its default namespace.
- Local wallpaper folders containing raster images. The plugin never starts a daemon or edits Hyprland configuration.

## Install explicitly

Close KITE. In a normal terminal, keep a persistent copy of this registry (skip cloning if you already have it):

```sh
mkdir -p "$HOME/Projects"
git clone https://github.com/Kabil777/kite_plugins.git "$HOME/Projects/kite_plugins"
cd "$HOME/Projects/kite_plugins"
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/kite/plugin"
ln -sT -- "$PWD/plugins/hyprland-wallpapers" "${XDG_CONFIG_HOME:-$HOME/.config}/kite/plugin/hyprland-wallpapers"
```

Use your actual checkout location if different. **If the destination exists, stop; do not force replacement or mix source and managed installs.** Keep the checkout in place.

## Choose your folders

1. Reopen KITE. Open **Plugin marketplace → Installed**, select **Hyprland Wallpapers**, then **Options → Settings**. Choose **Allow in KITE** if needed; an explicit YAML disable still takes precedence.
2. Paste a JSON list into **Wallpaper folders**, then save:

   ```json
   ["~/Pictures/Wallpapers", "/mnt/photos/wallpapers"]
   ```

3. Search KITE for **Hyprland Wallpapers** and open it. Search filenames/folders, press Enter to preview, then choose **Apply to all displays**. Cancel/Esc returns without applying.

The folder setting starts empty: installing or opening this plugin cannot change your wallpaper. Nested folders are included; hidden entries and nested symlinks are skipped. **Ctrl+R** refreshes the file list. All displays means all outputs of the default daemon, not every custom daemon namespace.

For daemon setup, limits and troubleshooting, see [HOWTO.md](HOWTO.md), also available through KITE's plugin help.

## Development check

With sibling `kite` and `kite_plugins` checkouts and KITE's uv environment prepared, run from the **registry root**:

```sh
PYTHONPATH=../kite PYTHONDONTWRITEBYTECODE=1 uv run --project ../kite --locked --no-sync python -m tests.check_wallpapers
```

Uses temporary XDG folders, synthetic images, a fake `awww`, and an offscreen Qt preview. Never contacts a real wallpaper daemon or changes the desktop. Plugins still retain your user's privileges; folder checks and systemd containment are not a permission sandbox.
