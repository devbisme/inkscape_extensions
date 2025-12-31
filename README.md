
# Inkscape Extensions

This repository contains some Inkscape extensions I built for personal use:

- `radial_binary_encoder.py` — Draws a radial disk that encodes a number in a binary-sector visual format.
- `split_regions.py` — Splits an image into separate image regions by detecting connected foreground regions.

**Files**
- [radial_binary_encoder.py](radial_binary_encoder.py)
- [radial_binary_encoder.inx](radial_binary_encoder.inx)
- [split_regions.py](split_regions.py)
- [split_regions.inx](split_regions.inx)

## radial_binary_encoder

This extension is for creating disks to play on a [child's toy gramophone](https://www.amazon.com/Gramophone-Learning-Storytelling-Toddler-Player/dp/B0DKHFRXSW?th=1). Each disk encodes a number
that's read by the gramophone and used to access a sound file for a song or story stored in the player.
The disk numbers and the title of their corresponding content are stored in `music_disks.ods`.

Function:
- Generates a circular graphic (67 mm outer diameter) that encodes a provided integer as a sequence of radial sectors. The extension draws the outer disk, encoded sectors (including a parity sector), an inner clear disk, a small triangular marker and the input number as text.

Usage:
- Run the extension from `Extensions → Custom → Radial Binary Encoder...`. Enter an integer value in the `number` field and apply.
- The extension creates a grouped SVG object with a unique id so you can move or edit it after creation.

Notes:
- The script computes a transformed 10-bit value from the supplied number and encodes that value plus parity in radial sectors.
- No external Python packages are required for this script beyond Inkex (the Inkscape extensions API).

## split_regions

This extension removes the background from an image and inserts any remaining connected components into the drawing.
Its main use is to remove *simple* backgrounds from images that are pasted into a drawing.

Function:
- Takes a selected raster image inside the SVG and slices it into multiple image fragments corresponding to connected foreground regions. The fragments are inserted into the SVG as separate embedded PNG images positioned to match the source image.

Key options:
- `bg_mode`: how to choose the background color — `border`, `manual`, or `pick` (pick uses the image transform center).
- `bg_color`: manual background color (hex).
- `tolerance`: color distance cutoff for detecting background pixels.
- `min_pixels`: ignore regions smaller than this number of pixels.

Usage:
- Select a raster image object in the document, then run the extension from `Extensions → Custom → Split Image into Regions...`. Adjust options and apply.

Dependencies:
- This extension uses Python packages that may not be included with Inkscape by default: `numpy`, `Pillow` (PIL), and `scipy` (for connected-component labeling and morphology). Install them in the same Python environment Inkscape uses for extensions.

Install command example (system Python environment):

```bash
python3 -m pip install --user numpy pillow scipy
```

## Installation (both extensions)

1. Copy the `.py` and corresponding `.inx` files to your Inkscape extensions directory:

   - Per-user: `~/.config/inkscape/extensions/`
   - System-wide: `/usr/share/inkscape/extensions/`

2. Make the Python scripts executable (optional but recommended):

```bash
chmod +x ~/.config/inkscape/extensions/radial_binary_encoder.py
chmod +x ~/.config/inkscape/extensions/split_regions.py
```

3. Restart Inkscape.

4. Open the Extensions menu and locate the installed extensions (their exact menu location may vary depending on Inkscape version and your system).

## Troubleshooting

- If an extension fails to run, check Inkscape's extensions console or run the script manually to see errors. Ensure required Python packages (`numpy`, `Pillow`, `scipy`) are installed and available to Inkscape's Python interpreter.
- For `split_regions.py`, make sure you select a raster image object before running the extension.

## License

The code in this repository is released under the MIT License.
