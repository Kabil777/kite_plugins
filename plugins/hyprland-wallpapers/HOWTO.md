# Use Hyprland Wallpapers

## Start the backend yourself

Install `awww` using your distribution's packages or [its upstream instructions](https://codeberg.org/LGFae/awww). This plugin uses **awww**, not an automatic `swww` fallback.

If no default `awww-daemon` is running, start it in a normal terminal inside your Hyprland session:

```sh
awww-daemon &
```

Do not start another copy if one is already running. For automatic startup, add it to your existing session startup configuration. In configurations using `hyprland.conf`, the usual entry is:

```ini
exec-once = awww-daemon
```

Use your current Hyprland startup mechanism for other configuration formats. KITE never creates this entry, starts/stops a daemon, or replaces an existing wallpaper service. Do not run competing wallpaper services on the same outputs.

## Configure folders through Plugin Settings

Open **Plugin marketplace → Installed → Hyprland Wallpapers → Options → Settings**. The one folder field holds a JSON list:

```json
["~/Pictures/Wallpapers", "/mnt/photos/wallpapers"]
```

Use double quotes and commas as shown. Spaces, commas and semicolons inside quoted folder names are supported. Use absolute paths or `~/`; shell variables such as `$HOME` are not expanded. Up to 16 folders fit in the 1,024-character setting. `[]` intentionally lists nothing.

Folders can be elsewhere on disk; they do not need to live in the plugin checkout. An explicitly configured folder may itself be a symlink; its current resolved target is the allowed root. Nested folder/file symlinks and hidden entries are skipped. Unavailable folders produce a warning while other configured folders remain usable.

Save before opening the tool. Do not edit a source file to configure personal folders, or commit personal settings to this repository.

## Pick, preview, apply

1. Search KITE for **Hyprland Wallpapers** and open it.
2. Type part of a filename or folder path. All search words must occur somewhere in the full path.
3. Select a result and press Enter. KITE shows its normal bounded image preview.
4. Press **Apply to all displays** to send exactly one `awww img -- /absolute/file` request. The file is rechecked against the current allowed folders and recorded identity before sending.
5. KITE returns to the list with a success notification when the client succeeds. Cancel/Esc before applying does not send a request.

No monitor selector, background rotation, random selection, daemon startup or arbitrary shell command is involved. The `--outputs` option is omitted, so all outputs in the default daemon namespace are targeted. The plugin does **not** use `--all`, which would affect other daemon namespaces too. Normal awww resize/transition defaults and inherited `AWWW_TRANSITION_*` settings remain in effect.

## Refresh and limits

The worker keeps a metadata-only file index so typing does not rescan folders on every keystroke. Use **Ctrl+R / Refresh wallpapers** after adding, moving or changing files. No persistent wallpaper index, image-content cache or list of recently applied images is written by this plugin. awww's own cache remains under awww's control.

- Recursive scan: at most 10,000 directory entries and 2,000 images. A limit warning means you should configure narrower folders.
- PNG, JPEG, WebP, GIF, BMP, TIFF and AVIF filenames are accepted; actual decoding depends on awww's build.
- Regular, nonempty files up to 32 MiB only. Unsupported, unreadable, oversized and invalid-UTF-8 filenames are skipped.
- At most 200 matches are returned per query; refine the search to find more.
- Qt previews have separate safety limits (16 MiB, 32 million pixels) and installed decoder requirements. A preview may be unavailable even if awww can display the file. Animated previews show a still frame.
- The awww client has a five-second deadline. Large/animated files may exceed it.

## Troubleshooting

- **No images:** save valid existing folders in Settings, check permissions and supported extensions, then refresh. Hidden files and nested symlinks are deliberately excluded.
- **File changed / selection expired:** return to the list, refresh and preview again. Deleted/replaced files are not silently substituted for the old selection.
- **awww not installed:** install it outside KITE. Nothing is compiled or downloaded by this plugin.
- **Daemon/session error:** confirm your default `awww-daemon` is running in the same Wayland session as KITE. A daemon started only under a custom namespace is not targeted.
- **Timeout or backend error:** some outputs may already have changed. Check the desktop before retrying; KITE does not retry or roll back automatically.

## Disable, update or remove

**Disallow in KITE** stops activation without touching wallpaper files or the daemon. For a source update, close KITE, review/pull changes in the linked registry checkout, and reopen it. For removal, close KITE and remove only the source link you created after checking its target. Never replace a manager-owned link by hand. None of these steps resets your wallpaper or deletes image folders.

Plugins have your user's privileges. The configured-folder checks prevent accidental out-of-scope selections, not access by hostile code or adversarial filesystem races. Cancelling after an apply request has been sent cannot undo a wallpaper change.
