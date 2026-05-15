# darktable gallery export

Load `gallery_export.lua` from your darktable `luarc`:

```lua
dofile("/Users/jsteward/work/jsteward.moe/imaging/darktable/gallery_export.lua")
```

The script adds a **gallery export** panel in lighttable and darkroom. Pick a
category, adjust the max width if needed, select images, and click
**export selected AVIF**. It writes max-width 3200px AVIF files into
`content/images/gallery/<category>/` by default.

A toast appears after each exported image with progress like `15/20 filename`.
Images with darktable's red color label are exported as `*-featured.avif`,
which makes them appear on the gallery Overview.

After export it runs `exiftool` and keeps only the fields used by
`imaging/gallery.py` for captions:

- `Make`
- `Model`
- `LensMake`
- `LensModel`
- `FocalLength`
- `FNumber`
- `ExposureTime`
- `ISO`
- `ISOSpeedRatings`
- `PhotographicSensitivity`
- `DateTimeOriginal`

If darktable cannot find `exiftool`, the script tries common macOS, NixOS, and
nix-darwin per-user profile paths. You can also launch darktable with `EXIFTOOL`
pointing at the binary, or set that variable in the environment used to start
darktable.
