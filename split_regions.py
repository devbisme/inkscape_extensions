#!/usr/bin/env python3
import inkex
import base64
import io
import tempfile
import numpy as np
import uuid
from math import sqrt
from PIL import Image
from scipy import ndimage
from urllib.request import pathname2url


class SplitRegions(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument(
            "--bg_mode", default="border", choices=["border", "manual", "pick"]
        )
        pars.add_argument("--bg_color", default="#000000")
        pars.add_argument("--tolerance", type=float, default=8.0)
        pars.add_argument("--min_pixels", type=int, default=0)

    def effect(self):
        # self.msg("Split Regions: starting")

        # Clamp tolerance to match expanded UI range (0 .. 442)
        max_tol = sqrt(3 * (255 ** 2))
        self.options.tolerance = min(max(self.options.tolerance, 0.0), max_tol)
        # self.msg(f"Using tolerance: {self.options.tolerance}")

        if not self.svg.selection:
            raise inkex.AbortExtension("Please select an image.")

        node = next(iter(self.svg.selection.values()))
        if node.tag != inkex.addNS("image", "svg"):
            raise inkex.AbortExtension("Selected object is not an image.")

        # self.msg("Image selected")

        # -------------------------------------------------
        # Load image
        # -------------------------------------------------
        href = node.get("{http://www.w3.org/1999/xlink}href")
        if href is None:
            raise inkex.AbortExtension("Image has no href.")

        if href.startswith("data:image"):
            # self.msg("Loading embedded image")
            data = base64.b64decode(href.split(",")[1])
            img = Image.open(io.BytesIO(data)).convert("RGBA")
        elif href.startswith("file://"):
            # self.msg("Loading linked image")
            path = inkex.utils.uri_to_path(href)
            img = Image.open(path).convert("RGBA")
        else:
            raise inkex.AbortExtension("Unsupported image reference.")

        arr = np.array(img)
        img_h_px, img_w_px, _ = arr.shape

        # -------------------------------------------------
        # Un-premultiply alpha
        # -------------------------------------------------
        rgb = arr[:, :, :3].astype(float)
        alpha = arr[:, :, 3:4] / 255.0
        alpha[alpha == 0] = 1.0
        arr[:, :, :3] = np.clip(rgb / alpha, 0, 255).astype(np.uint8)

        # -------------------------------------------------
        # Determine background color
        # -------------------------------------------------
        if self.options.bg_mode == "border":
            # self.msg("Background mode: border")
            border = np.concatenate(
                [arr[0, :, :3], arr[-1, :, :3], arr[:, 0, :3], arr[:, -1, :3]]
            )
            bg_color = np.median(border, axis=0)

        elif self.options.bg_mode == "manual":
            # self.msg("Background mode: manual hex")
            s = str(self.options.bg_color).strip()
            if s.startswith("#"):
                s = s[1:]
            if len(s)%3 != 0:
                raise inkex.AbortExtension("Background color must be in #RGB, #RRGGBB, #RRRGGGBBB format.")
            try:
                w = len(s) // 3
                r, g, b = [int(s[i*w:(i+1)*w], 16) // (16**(w-2)) for i in range(3)]
            except ValueError:
                raise inkex.AbortExtension("Background color must be a valid hexadecimal #RRGGBB.")
            bg_color = np.array([r, g, b])

        else:  # pick
            # self.msg("Background mode: click-to-pick")

            cx = node.get(inkex.addNS("transform-center-x", "inkscape"))
            cy = node.get(inkex.addNS("transform-center-y", "inkscape"))

            if cx is None or cy is None:
                raise inkex.AbortExtension(
                    "Set the transform center on the image to pick a color."
                )

            cx = float(cx)
            cy = float(cy)

            svg_w = float(node.get("width"))
            svg_h = float(node.get("height"))

            px = int(((cx+svg_w/2) / svg_w) * img_w_px)
            py = int(((-cy+svg_h/2) / svg_h) * img_h_px)

            # self.msg(f"svg_w_h=({svg_w}, {svg_h}) img_w_h=({img_w_px}, {img_h_px})")
            # self.msg(f"Picking pixel at SVG coords ({cx}, {cy}) -> image ({px}, {py})")

            px = np.clip(px, 0, img_w_px - 1)
            py = np.clip(py, 0, img_h_px - 1)

            bg_color = arr[py, px, :3]
            bg_color = bg_color.astype(np.int64)

        # self.msg(f"Background color: {bg_color}")

        # -------------------------------------------------
        # Foreground mask
        # -------------------------------------------------
        diff = np.linalg.norm(arr[:, :, :3] - bg_color, axis=2)
        foreground = diff > self.options.tolerance

        structure = np.ones((3, 3), dtype=bool)
        foreground = ndimage.binary_opening(foreground, structure)
        foreground = ndimage.binary_closing(foreground, structure)
        foreground = ndimage.binary_fill_holes(foreground)

        labels, num = ndimage.label(foreground, structure)
        # self.msg(f"Found {num} connected regions")

        # -------------------------------------------------
        # SVG scaling
        # -------------------------------------------------
        x = float(node.get("x", "0"))
        y = float(node.get("y", "0"))
        svg_w = float(node.get("width"))
        svg_h = float(node.get("height"))

        scale_x = svg_w / img_w_px
        scale_y = svg_h / img_h_px

        # -------------------------------------------------
        # Group with transform
        # -------------------------------------------------
        parent = node.getparent()

        group = inkex.Group()
        group.set("id", f"split-regions-{uuid.uuid4().hex}")
        group.label = "Split Regions"

        if "transform" in node.attrib:
            group.set("transform", node.get("transform"))

        # insert the new group right after the image node (safer than appending)
        try:
            idx = parent.index(node)
            parent.insert(idx + 1, group)
        except ValueError:
            parent.add(group)

        # -------------------------------------------------
        # Insert regions
        # -------------------------------------------------
        count = 0

        for label_id in range(1, num + 1):
            mask = labels == label_id
            if self.options.min_pixels > 0 and mask.sum() < self.options.min_pixels:
                continue

            coords = np.argwhere(mask)
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0) + 1

            region = arr[y0:y1, x0:x1].copy()
            region[~mask[y0:y1, x0:x1]] = [0, 0, 0, 0]

            buf = io.BytesIO()
            Image.fromarray(region).save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            uri = "data:image/png;base64," + b64

            new_img = inkex.Image()
            new_img.set("{http://www.w3.org/1999/xlink}href", uri)
            new_img.set("x", str(x + x0 * scale_x))
            new_img.set("y", str(y + y0 * scale_y))
            new_img.set("width", str((x1 - x0) * scale_x))
            new_img.set("height", str((y1 - y0) * scale_y))

            group.add(new_img)
            count += 1

        # self.msg(f"Done. Inserted {count} regions.")


if __name__ == "__main__":
    SplitRegions().run()
