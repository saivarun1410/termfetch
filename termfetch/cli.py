"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from . import art as art_mod
from . import gh, svg, theme as theme_mod

# A placeholder that survived substitution, i.e. one we had no value for.
UNRESOLVED = re.compile(r"\{\{[a-zA-Z_][a-zA-Z0-9_]*\}\}")

DEFAULTS: dict = {
    "image": None,
    "imageCrop": None,
    "imageCols": 56,
    "charset": "blocks",
    "coloredImage": True,
    "contrast": 1.2,
    "brightness": 1.0,
    "gamma": 1.05,
    "colorStep": 8,
    "invert": False,
    "theme": "github-dark",
    "colors": None,
    "windowTitle": "{{username}}@github",
    "chrome": True,
    "fontSize": 13,
    "keyWidth": 13,
    "panelAlign": "top",
    "github": None,
    "languageMode": "repos",
    "topLanguages": 5,
    "sections": [],
}


def load_config(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    unknown = set(raw) - set(DEFAULTS)
    if unknown:
        raise SystemExit(f"unknown config keys: {sorted(unknown)}")
    cfg = {**DEFAULTS, **raw}
    if not isinstance(cfg["sections"], list) or not cfg["sections"]:
        raise SystemExit("config needs a non-empty 'sections' array")
    return cfg


def build_sections(cfg: dict, variables: dict[str, str]) -> list[svg.Section]:
    out = []
    for raw in cfg["sections"]:
        title = raw.get("title")
        if title is not None:
            title = gh.apply_templates(str(title), variables)
        fields = []
        for field in raw.get("fields", []):
            if isinstance(field, str):
                key, value = "", field
            elif isinstance(field, (list, tuple)) and len(field) == 2:
                key, value = field
            elif isinstance(field, dict):
                key, value = field.get("key", ""), field.get("value", "")
            else:
                raise SystemExit(f"bad field entry: {field!r}")
            value = gh.apply_templates(str(value), variables)
            # Drop the row if the value came out empty, or if it still references a
            # variable we have no data for. Either way there is nothing to show, and a
            # literal "{{bio}}" on the card is worse than an absent line.
            if not value.strip() or UNRESOLVED.search(value):
                continue
            fields.append((str(key), value))
        if fields or title:
            out.append(svg.Section(title, fields))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="termfetch", description="Generate a neofetch-style profile card as SVG.")
    ap.add_argument("--config", type=Path, required=True, help="path to config.json")
    ap.add_argument("--out", type=Path, required=True, help="path to write the SVG")
    ap.add_argument("--user", help="GitHub username (overrides config 'github')")
    ap.add_argument("--token", help="GitHub token; defaults to $GITHUB_TOKEN")
    ap.add_argument("--no-fetch", action="store_true", help="skip the GitHub API; leave variables blank")
    ap.add_argument("--preview", type=Path, help="also write a plain-text version of the art")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    base = args.config.parent

    variables: dict[str, str] = {}
    user = args.user or cfg.get("github")
    if user and not args.no_fetch:
        try:
            variables = gh.fetch(
                user,
                args.token or os.environ.get("GITHUB_TOKEN"),
                top_languages=int(cfg["topLanguages"]),
                language_mode=str(cfg["languageMode"]),
            )
        except gh.GitHubError as exc:
            print(f"warning: {exc}; rendering without live stats", file=sys.stderr)
            variables = {"username": user, "name": user}
    elif user:
        variables = {"username": user, "name": user}

    picture = None
    if cfg["image"]:
        image_path = Path(cfg["image"])
        if not image_path.is_absolute():
            image_path = base / image_path
        crop = cfg["imageCrop"]
        picture = art_mod.render(
            str(image_path),
            cols=int(cfg["imageCols"]),
            charset=cfg["charset"],
            colored=bool(cfg["coloredImage"]),
            mono_color=theme_mod.get(cfg["theme"]).mono,
            crop=tuple(crop) if crop else None,
            # Keep the sampling grid tied to the renderer's real cell shape.
            char_aspect=svg.CHAR_WIDTH_RATIO,
            contrast=float(cfg["contrast"]),
            brightness=float(cfg["brightness"]),
            gamma=float(cfg["gamma"]),
            color_step=int(cfg["colorStep"]),
            invert=bool(cfg["invert"]),
        )

    active = theme_mod.get(cfg["theme"]).merged(cfg["colors"])
    layout = svg.Layout(
        font_size=float(cfg["fontSize"]),
        chrome=bool(cfg["chrome"]),
        key_width=int(cfg["keyWidth"]),
        panel_align=str(cfg["panelAlign"]),
    )
    title = gh.apply_templates(str(cfg["windowTitle"] or ""), variables)

    document = svg.build(picture, build_sections(cfg, variables), active, layout, title)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(document, encoding="utf-8")
    print(f"wrote {args.out} ({len(document) // 1024} KB)")

    if args.preview and picture:
        args.preview.write_text(picture.as_text() + "\n", encoding="utf-8")
        print(f"wrote {args.preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
