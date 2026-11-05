# Use Hyprland Wallpapers

## Backend setup

Install [awww](https://codeberg.org/LGFae/awww) using your distribution's packages. If no default daemon is running, start it in a normal terminal **inside your Hyprland session**:

```sh
awww-daemon &
```

Do not start a second copy. For `hyprland.conf` profiles, normal session autostart can use `exec-once = awww-daemon`; other configuration formats should use their existing startup mechanism. KITE never writes this configuration, starts/stops daemons or replaces competing wallpaper services. This plugin uses awww, not a silent swww fallback.

**Host compatibility:** update KITE and this source package together to current main, then close/reopen KITE. Original v0.1.0 assets do not include typed Settings, the save/navigation fixes or this split-view contract. No Rust compiler is needed for the plugin.

## Add folders without JSON

Open **Plugin marketplace → Installed → Hyprland Wallpapers → Options → Settings**, or the browser's **Settings** button / **Actions → Plugin Settings**.

- **Browse** selects a folder. Alternatively enter an absolute path or `~/Pictures/Wallpapers`, then click **Add**.
- Double-click an item to edit; **Remove** deletes the selected entry; **Clear** empties the list.
- **Save configuration** writes your preferences. Missing/unmounted folders warn when browsed, while available folders remain usable.
- Up to 16 folders, 4,096 characters per path and 16 KiB total plugin settings. Spaces, commas and semicolons are literal path characters; `$HOME` shell expansion is not performed.

Folders need not live in the checkout. An explicitly configured folder symlink resolves to its allowed target; nested folder/file symlinks and hidden entries are excluded. An empty list intentionally scans nothing. Existing valid JSON-array strings migrate in memory and are written as YAML lists only on explicit Save. Malformed legacy data remains an error: use Clear/Add/Browse to repair it instead of silently losing the old setting.

Saving is asynchronous. On failure, your draft stays editable and disk is unchanged. If another process changed the same values, reopen Settings rather than overwriting them. **Saved; reload needed** means the file was committed but refreshing the worker failed; it is not a rolled-back save.

## Browse and apply

Search filenames/folders; all words must occur in the full path. Choose **All folders** or a configured folder from the dropdown. Single-click/↑/↓ updates the large preview; it does not call awww. Thumbnails and preview decoding run in bounded background jobs. Narrow windows stack the detail below the list; quick controls remain available through Options.

**Enter / Apply to all displays** explicitly sends one validated request for the selected file. The file's allowed-folder scope and recorded identity are rechecked immediately before execution. There is no separate Apply confirmation tab. Escape/Back before applying does not send a change.

All displays means every output of the default awww daemon namespace: no `--outputs` restriction and no `--all` flag. There is no monitor selector, random-image picker, background rotation, raw shell command or desktop-changing preview. Choosing a random **transition** does not choose a random image.

## Image and transition options

Quick controls expose **Fit**, **Transition** and **Duration**. **Options…** opens the same contract-driven editor used by Settings. Changes here affect only the session/next Apply; **Save defaults** explicitly persists them. **Reset** returns session options to unset/backend inheritance. Permanent defaults can also be edited in Plugin Settings.

Check **Default / Backend default** to leave an option unset. Unset options do not generate CLI flags, so awww defaults and inherited `AWWW_TRANSITION_*` variables remain effective. Explicit false Y-inversion overrides inherited `INVERT_Y=true` without pretending that omitting a flag means false.

| Control | Meaning |
| --- | --- |
| Fit | Crop/fill, fit the whole image, stretch, or original size (`no`) |
| Crop position | Nine anchors; requires crop mode |
| Padding color | RGB/RGBA hexadecimal, including alpha, via a native color picker |
| Scaling filter | Nearest, Bilinear, CatmullRom, Mitchell or Lanczos3 |
| Transition | none, simple, fade, left/right/top/bottom, wipe, wave, grow, center, any, outer or random |
| Duration | Seconds, 0–120; **not used by simple or none** |
| Step | 1–255; controls simple speed (awww normally uses 2); 255 is immediate |
| FPS | 1–240, a KITE safety range; awww normally uses 30 |
| Angle | Wipe/wave degrees, −360 to 360 |
| Position | Named anchor or custom fraction/pixel X/Y; both custom coordinates are required |
| Bézier | Four numeric control coordinates, −10 to 10; set all together; all-zero is invalid |
| Wave | Width and height together, 0.001–10,000 |
| Invert Y | Flip the transition origin's Y coordinate |

Custom fraction coordinates use 0–1; pixel coordinates must be whole numbers up to 32,768. The backend preserves the decimal representation of fraction `1.0`, because awww interprets integer `1` as a pixel coordinate. The bounds above are KITE's documented UI/safety policy, not a claim that every awww CLI range is identical.

The in-app still preview preserves the source image's aspect ratio. It is not a compositor simulation of cropping/transitions; Apply lets awww perform the actual resize and animation.

CLI behavior was checked against awww v0.12.1 [argument definitions](https://codeberg.org/LGFae/awww/src/tag/v0.12.1/client/src/cli.rs) and [client request handling](https://codeberg.org/LGFae/awww/src/tag/v0.12.1/client/src/main.rs). No upstream implementation is bundled.

## Refresh, bounds and failures

- **Ctrl+R / Refresh wallpapers** rebuilds the worker's metadata index after files are added/changed. It is not a filesystem watcher.
- At most 10,000 directory entries, 2,000 indexed images and 200 matches per query. Narrow folders/refine the search if a limit is reached.
- Supported raster filenames: PNG, JPEG, WebP, GIF, BMP, TIFF and AVIF. Regular, nonempty files up to 32 MiB; unreadable, oversized, hidden, symlinked and invalid-UTF-8 entries are skipped.
- Host previews have separate limits: 16 MiB, 32 million pixels, installed Qt decoder availability. Animated files show a still frame. A preview can be unavailable while awww can still display the file; the selected filename remains explicit.
- Image jobs: two decoders, bounded queue and 32-MiB decoded cache, all in memory. No persistent image/index/recent-wallpaper cache is written by this plugin; awww manages its own cache.
- The client deadline is five seconds, independent of transition animation duration. Large/animated preprocessing or a stalled daemon can exceed it.
- A client error or timeout may happen after some outputs changed. Check the desktop before retrying; KITE neither retries nor rolls back automatically.
- Changed/deleted/replaced files require Refresh and a new selection; they are not silently substituted for an old result.

**Blank/old Settings or apparent save/navigation freeze:** close the old KITE process and use the matching updated host. Typed Settings keep the draft on error and retire the completed form so hidden dirty state cannot block Back/Close.

## Disable, update or remove

**Disallow in KITE** prevents activation without changing image folders or the daemon. Close KITE before updating a source checkout, review/pull both compatible core and plugin changes, then reopen. For removal, inspect and remove only the authored source link you created; never replace or delete a manager-owned link manually. No step here resets your wallpaper or deletes images.

Plugins retain your user's privileges. Allowed-folder checks are safeguards against accidental selection, not a hostile-code or adversarial-filesystem sandbox. Cancelling after a request was sent cannot undo a wallpaper change.
