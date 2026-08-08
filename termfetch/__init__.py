"""termfetch — a neofetch-style terminal profile card, rendered to SVG."""

__version__ = "0.1.0"

from . import art, gh, svg, theme  # noqa: F401

__all__ = ["art", "gh", "svg", "theme", "__version__"]
