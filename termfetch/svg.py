"""Assemble the card SVG.

Every glyph is positioned with an explicit ``x``, so the card lays out identically no
matter which monospace font the viewer's browser falls back to. SVGs embedded in a
GitHub README render as images, which means webfonts never load — relying on the
font's own advance width would let the columns drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass

from .art import Art
from .theme import Theme

FONT_STACK = "ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace"

# Advance width of one character as a fraction of the font size. 0.6 is the standard
# ratio for the fonts in FONT_STACK.
CHAR_WIDTH_RATIO = 0.6


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


@dataclass
class Section:
    title: str | None
    fields: list[tuple[str, str]]


@dataclass
class Layout:
    font_size: float = 13.0
    line_height: float = 1.55  # multiplier, for the text panel
    padding: float = 22.0
    gap: float = 26.0  # between art and text panel
    chrome: bool = True  # draw the title bar with window buttons
    chrome_height: float = 30.0
    radius: float = 8.0
    key_width: int = 13  # characters reserved for the key column
    panel_align: str = "top"  # "top" or "middle", relative to the art

    @property
    def char_width(self) -> float:
        return self.font_size * CHAR_WIDTH_RATIO

    @property
    def text_line(self) -> float:
        return self.font_size * self.line_height

    @property
    def art_line(self) -> float:
        """Art rows are exactly one em tall so block glyphs tile without gaps."""
        return self.font_size


def _art_svg(art: Art, x0: float, y0: float, lay: Layout) -> list[str]:
    cw, lh = lay.char_width, lay.art_line
    out = []
    for r, row in enumerate(art.rows):
        # Baseline sits near the bottom of the cell; 0.82em matches typical mono metrics.
        y = y0 + r * lh + lh * 0.82
        spans, run_start, run_color, run_chars = [], 0, None, []

        def flush():
            if run_chars and run_color:
                spans.append(
                    f'<tspan x="{x0 + run_start * cw:.2f}" fill="{run_color}">'
                    f"{escape(''.join(run_chars))}</tspan>"
                )

        for c, cell in enumerate(row):
            if cell.color != run_color:
                flush()
                run_start, run_color, run_chars = c, cell.color, [cell.char]
            else:
                run_chars.append(cell.char)
        flush()
        if spans:
            out.append(f'<text y="{y:.2f}">{"".join(spans)}</text>')
    return out


def _panel_svg(
    sections: list[Section], x0: float, y0: float, lay: Layout, theme: Theme
) -> tuple[list[str], float, int]:
    """Return (svg lines, height consumed, widest line in characters)."""
    cw, lh = lay.char_width, lay.text_line
    out: list[str] = []
    row = 0
    widest = 0

    for i, section in enumerate(sections):
        if i:
            row += 0.5  # breathing room between sections
        if section.title is not None:
            y = y0 + row * lh + lh * 0.75
            out.append(
                f'<text x="{x0:.2f}" y="{y:.2f}" fill="{theme.title}" '
                f'font-weight="bold">{escape(section.title)}</text>'
            )
            widest = max(widest, len(section.title))
            row += 1
            # Underline the section heading the way neofetch does.
            rule = "─" * max(len(section.title), 1)
            y = y0 + row * lh + lh * 0.75
            out.append(
                f'<text x="{x0:.2f}" y="{y:.2f}" fill="{theme.separator}">{escape(rule)}</text>'
            )
            row += 1

        for key, value in section.fields:
            y = y0 + row * lh + lh * 0.75
            if not key:  # a full-width line, no key column
                out.append(
                    f'<text x="{x0:.2f}" y="{y:.2f}" fill="{theme.value}">{escape(value)}</text>'
                )
                widest = max(widest, len(value))
            else:
                vx = x0 + lay.key_width * cw
                out.append(
                    f'<text y="{y:.2f}">'
                    f'<tspan x="{x0:.2f}" fill="{theme.key}" font-weight="bold">{escape(key)}</tspan>'
                    f'<tspan x="{vx:.2f}" fill="{theme.value}">{escape(value)}</tspan>'
                    f"</text>"
                )
                widest = max(widest, lay.key_width + len(value))
            row += 1

    return out, row * lh, widest


def build(
    art: Art | None,
    sections: list[Section],
    theme: Theme,
    lay: Layout | None = None,
    title: str = "",
) -> str:
    lay = lay or Layout()
    cw = lay.char_width

    top = lay.padding + (lay.chrome_height if lay.chrome else 0)
    art_w = art.width * cw if art else 0.0
    art_h = art.height * lay.art_line if art else 0.0

    panel_x = lay.padding + (art_w + lay.gap if art else 0)
    # Measure first, then lay out again at the final offset — the panel's height is only
    # known once the sections have been walked, and centring needs it up front.
    _, panel_h, panel_chars = _panel_svg(sections, panel_x, top, lay, theme)
    panel_y = top
    if lay.panel_align == "middle" and art_h > panel_h:
        panel_y = top + (art_h - panel_h) / 2
    elif lay.panel_align not in ("top", "middle"):
        raise ValueError(f"panel_align must be 'top' or 'middle', got {lay.panel_align!r}")
    panel_lines, _, _ = _panel_svg(sections, panel_x, panel_y, lay, theme)
    panel_w = panel_chars * cw

    width = panel_x + panel_w + lay.padding
    height = top + max(art_h, panel_h) + lay.padding

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
        f'aria-label="{escape(title or "terminal profile card")}">',
        f"<title>{escape(title or 'profile card')}</title>",
        f'<rect width="{width:.0f}" height="{height:.0f}" rx="{lay.radius}" '
        f'fill="{theme.background}" stroke="{theme.border}"/>',
    ]

    if lay.chrome:
        parts.append(
            f'<path d="M0 {lay.radius} A{lay.radius} {lay.radius} 0 0 1 {lay.radius} 0 '
            f'H{width - lay.radius:.0f} A{lay.radius} {lay.radius} 0 0 1 {width:.0f} {lay.radius} '
            f'V{lay.chrome_height} H0 Z" fill="{theme.chrome}"/>'
        )
        for i, colour in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
            parts.append(
                f'<circle cx="{18 + i * 18}" cy="{lay.chrome_height / 2:.0f}" r="5.5" fill="{colour}"/>'
            )
        if title:
            parts.append(
                f'<text x="{width / 2:.0f}" y="{lay.chrome_height / 2 + 4:.0f}" '
                f'text-anchor="middle" fill="{theme.value}" opacity="0.65" '
                f'font-size="{lay.font_size - 1:.0f}">{escape(title)}</text>'
            )

    parts.append(
        f'<g font-family="{FONT_STACK}" font-size="{lay.font_size}" '
        f'xml:space="preserve" dominant-baseline="alphabetic">'
    )
    if art:
        parts += _art_svg(art, lay.padding, top, lay)
    parts += panel_lines
    parts += ["</g>", "</svg>"]
    return "\n".join(parts) + "\n"
