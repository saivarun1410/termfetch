"""Turn an image into a grid of coloured characters."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageEnhance

# Luminance ramps, darkest first. The renderer picks a character by pixel brightness.
RAMPS = {
    # Classic neofetch-ish ASCII. Reads as art at small sizes.
    "ascii": " .`':,^;~-+=*x?%#&@$",
    # Unicode shade blocks. Smoother gradient, still obviously "terminal".
    "blocks": " ░▒▓█",
    # Every cell a full block: the image is reproduced as flat colour, no texture.
    "solid": "█",
}

# Width divided by height of one character cell. Must match the geometry the renderer
# actually uses (svg.CHAR_WIDTH_RATIO over a one-em line height) or the art comes out
# stretched along one axis.
DEFAULT_CHAR_ASPECT = 0.6


@dataclass(frozen=True)
class Cell:
    char: str
    color: str  # "#rrggbb"


@dataclass(frozen=True)
class Art:
    rows: list[list[Cell]]

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return max((len(r) for r in self.rows), default=0)

    def as_text(self) -> str:
        """Plain-text version, for previewing in a terminal."""
        return "\n".join("".join(c.char for c in row) for row in self.rows)

    def as_ansi(self) -> str:
        out = []
        for row in self.rows:
            line = []
            for cell in row:
                r, g, b = (int(cell.color[i : i + 2], 16) for i in (1, 3, 5))
                line.append(f"\x1b[38;2;{r};{g};{b}m{cell.char}")
            out.append("".join(line) + "\x1b[0m")
        return "\n".join(out)


def _quantize_channel(value: int, step: int) -> int:
    """Snap a channel to a coarser grid so neighbouring cells share colours.

    Identical adjacent colours collapse into a single SVG span, which cuts the output
    size substantially on photographic input.
    """
    if step <= 1:
        return value
    return min(255, (value + step // 2) // step * step)


def render(
    path: str,
    cols: int = 56,
    charset: str = "ascii",
    colored: bool = True,
    mono_color: str = "#c9d1d9",
    crop: tuple[int, int, int, int] | None = None,
    char_aspect: float = DEFAULT_CHAR_ASPECT,
    contrast: float = 1.0,
    brightness: float = 1.0,
    gamma: float = 1.0,
    color_step: int = 8,
    invert: bool = False,
) -> Art:
    """Render ``path`` as a grid of coloured characters.

    ``crop`` is an (x, y, w, h) box applied before scaling. ``cols`` sets the width in
    characters; the row count follows from the image aspect ratio and ``char_aspect``.
    """
    if charset not in RAMPS:
        raise ValueError(f"unknown charset {charset!r}; expected one of {sorted(RAMPS)}")
    ramp = RAMPS[charset]

    img = Image.open(path).convert("RGB")
    if crop:
        x, y, w, h = crop
        img = img.crop((x, y, x + w, y + h))

    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)

    rows = max(1, round(cols * char_aspect * img.height / img.width))
    img = img.resize((cols, rows), Image.LANCZOS)

    grid: list[list[Cell]] = []
    for y in range(rows):
        line: list[Cell] = []
        for x in range(cols):
            r, g, b = img.getpixel((x, y))
            # Rec. 709 luma; matches how bright the colour actually looks.
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            if gamma != 1.0:
                lum = lum ** (1.0 / gamma)
            if invert:
                lum = 1.0 - lum
            char = ramp[min(len(ramp) - 1, int(lum * len(ramp)))]

            if colored:
                color = "#%02x%02x%02x" % (
                    _quantize_channel(r, color_step),
                    _quantize_channel(g, color_step),
                    _quantize_channel(b, color_step),
                )
            else:
                color = mono_color
            line.append(Cell(char, color))
        grid.append(line)

    return Art(grid)
