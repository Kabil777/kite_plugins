# Hyprland Wallpapers for KITE

Browse a thumbnail list with a large selection preview, choose awww image/transition options, then **Apply to all displays**. Selection never changes your wallpaper.

**Optional source plugin.** Not installed by default; no marketplace archive is published yet. Use **current KITE main with typed Settings and split previews**—the original v0.1.0 app release is too old for this contract. Python/Qt still owns the UI; no extra Python dependencies or Rust build is needed.

## Requirements

- [Updated KITE](https://github.com/Kabil777/kite), systemd user session and cgroup v2 tool-worker support.
- Hyprland/Wayland, `awww`, and an existing default-namespace `awww-daemon` in the same session.
- Local raster-image folders. The plugin does not install dependencies, start a daemon or edit Hyprland configuration.

## Install explicitly

Close KITE. In a normal terminal, clone this registry if you do not already have it:

```sh
mkdir -p "$HOME/Projects"
git clone https://github.com/Kabil777/kite_plugins.git "$HOME/Projects/kite_plugins"
cd "$HOME/Projects/kite_plugins"
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/kite/plugin"
ln -sT -- "$PWD/plugins/hyprland-wallpapers" "${XDG_CONFIG_HOME:-$HOME/.config}/kite/plugin/hyprland-wallpapers"
```

Use your actual checkout location. **If the destination exists, stop; do not force replacement or mix source/managed installs.** Keep the linked checkout in place. Update KITE and this package together, then reopen KITE.

## Configure and use

1. **Plugin marketplace → Installed → Hyprland Wallpapers → Options → Settings**. Choose **Allow in KITE** if needed; YAML disables still take precedence.
2. Under **Wallpaper folders**, use **Browse** or enter a folder and click **Add**, then **Save configuration**. No JSON editing. Existing valid JSON-list settings load automatically and become typed lists only on Save.
3. Open **Hyprland Wallpapers** from KITE search. Click or use ↑/↓ to preview; use the folder dropdown to narrow the list.
4. Adjust Fit/Transition/Duration, or open **Options…** for the remaining awww controls. These edits are temporary. **Save defaults** explicitly remembers them; **Reset** restores backend-default inheritance in the session.
5. **Enter / Apply to all displays** changes the wallpaper. **Ctrl+R** refreshes files. Settings can also be opened from the browser or its Actions.

Leave **Default** checked to inherit awww behavior/environment. Duration is not used by `simple` or `none`; simple speed uses **Transition step**. All displays targets default-namespace outputs, not every daemon namespace.

See [HOWTO.md](HOWTO.md) for detailed controls, limits, daemon setup and removal.

## Development checks

With sibling `kite` and `kite_plugins` checkouts and KITE's uv environment ready:

```sh
# From the registry root: fixture files and a fake awww only.
PYTHONPATH=../kite PYTHONDONTWRITEBYTECODE=1 uv run --project ../kite --locked --no-sync python -m tests.check_wallpapers
# From the KITE root: real offscreen Qt browser/settings/save integration.
QT_QPA_PLATFORM=offscreen uv run --locked --no-sync python -m tests.check_catalog_detail
QT_QPA_PLATFORM=offscreen uv run --locked --no-sync python -m tests.check_plugin_settings
```

No live wallpaper, daemon or private image folder is used. Plugins retain your user's privileges; folder validation and containment are not a permission sandbox.
