import datetime as dt
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from termfetch import art, cli, gh, svg, theme  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def photo(tmp_path):
    """A 200x200 image: black left half, white right half."""
    img = Image.new("RGB", (200, 200), (0, 0, 0))
    for x in range(100, 200):
        for y in range(200):
            img.putpixel((x, y), (255, 255, 255))
    p = tmp_path / "photo.png"
    img.save(p)
    return str(p)


# --- art -------------------------------------------------------------------


def test_grid_dimensions_follow_aspect_ratio(photo):
    a = art.render(photo, cols=50, char_aspect=0.6)
    assert a.width == 50
    # square source, so rows = cols * char_aspect
    assert a.height == 30


def test_non_square_source_is_not_distorted(photo, tmp_path):
    wide = tmp_path / "wide.png"
    Image.new("RGB", (400, 100), (128, 128, 128)).save(wide)
    a = art.render(str(wide), cols=60, char_aspect=0.6)
    assert a.height == round(60 * 0.6 * 100 / 400)


def test_brightness_maps_to_ramp_ends(photo):
    a = art.render(photo, cols=20, charset="ascii", colored=False)
    ramp = art.RAMPS["ascii"]
    row = a.rows[0]
    assert row[0].char == ramp[0]  # black -> first ramp entry
    assert row[-1].char == ramp[-1]  # white -> last


def test_invert_flips_the_mapping(photo):
    normal = art.render(photo, cols=20, charset="ascii", invert=False)
    flipped = art.render(photo, cols=20, charset="ascii", invert=True)
    assert normal.rows[0][0].char == flipped.rows[0][-1].char


def test_crop_selects_a_region(photo):
    a = art.render(photo, cols=10, charset="ascii", crop=(0, 0, 100, 100), colored=False)
    ramp = art.RAMPS["ascii"]
    # cropped to the black half only
    assert {c.char for row in a.rows for c in row} == {ramp[0]}


def test_mono_uses_a_single_colour(photo):
    a = art.render(photo, cols=10, colored=False, mono_color="#abcdef")
    assert {c.color for row in a.rows for c in row} == {"#abcdef"}


def test_quantisation_reduces_distinct_colours(photo, tmp_path):
    noisy = tmp_path / "noisy.png"
    img = Image.new("RGB", (64, 64))
    for x in range(64):
        for y in range(64):
            img.putpixel((x, y), (x * 4 % 256, y * 4 % 256, (x + y) * 2 % 256))
    img.save(noisy)
    fine = art.render(str(noisy), cols=40, color_step=1)
    coarse = art.render(str(noisy), cols=40, color_step=64)
    n = lambda a: len({c.color for row in a.rows for c in row})  # noqa: E731
    assert n(coarse) < n(fine)


def test_unknown_charset_rejected(photo):
    with pytest.raises(ValueError, match="unknown charset"):
        art.render(photo, charset="nope")


def test_halfblocks_double_the_vertical_samples(photo):
    plain = art.render(photo, cols=40, charset="blocks", char_aspect=0.6)
    half = art.render(photo, cols=40, charset="halfblocks", char_aspect=0.6)
    # same number of text rows, but each carries two pixels
    assert half.height == plain.height
    assert all(c.bg is not None for row in half.rows for c in row)
    assert all(c.char == art.HALF_BLOCK for row in half.rows for c in row)


def test_halfblocks_sample_distinct_upper_and_lower_pixels(tmp_path):
    """A one-pixel-tall stripe must survive, which it cannot without half-blocks."""
    img = Image.new("RGB", (40, 40), (0, 0, 0))
    for x in range(40):
        for y in range(0, 40, 2):
            img.putpixel((x, y), (255, 255, 255))
    p = tmp_path / "stripes.png"
    img.save(p)
    a = art.render(str(p), cols=40, charset="halfblocks", char_aspect=0.5, color_step=1)
    assert any(c.color != c.bg for row in a.rows for c in row)


def test_halfblock_cells_render_background_rects(photo):
    a = art.render(photo, cols=20, charset="halfblocks")
    doc = svg.build(a, [svg.Section(None, [("K", "v")])], theme.get("github-dark"))
    root = ET.fromstring(doc)
    ns = "{http://www.w3.org/2000/svg}"
    # one background rect per colour run, plus the card's own background rect
    assert len(list(root.iter(f"{ns}rect"))) > 1
    ET.fromstring(doc)


def test_matching_pixel_pair_needs_no_glyph(tmp_path):
    """A flat image should be all rects and no art glyphs — the size optimisation."""
    flat = tmp_path / "flat.png"
    Image.new("RGB", (40, 40), (10, 20, 30)).save(flat)
    a = art.render(str(flat), cols=20, charset="halfblocks")
    doc = svg.build(a, [svg.Section(None, [(None, "x")])], theme.get("github-dark"))
    root = ET.fromstring(doc)
    ns = "{http://www.w3.org/2000/svg}"
    assert not any(s.text == art.HALF_BLOCK for s in root.iter(f"{ns}tspan"))


# --- svg -------------------------------------------------------------------


def test_output_is_well_formed_xml(photo):
    a = art.render(photo, cols=12)
    doc = svg.build(a, [svg.Section("Title", [("Key", "value")])], theme.get("github-dark"))
    ET.fromstring(doc)  # raises if malformed


def test_markup_in_values_is_escaped(photo):
    doc = svg.build(
        None,
        [svg.Section(None, [("K", '<script>alert("x")</script> & co')])],
        theme.get("github-dark"),
    )
    assert "<script>" not in doc
    assert "&lt;script&gt;" in doc
    ET.fromstring(doc)


def test_every_span_is_absolutely_positioned(photo):
    a = art.render(photo, cols=12)
    doc = svg.build(a, [svg.Section(None, [("K", "v")])], theme.get("github-dark"))
    root = ET.fromstring(doc)
    ns = "{http://www.w3.org/2000/svg}"
    spans = root.iter(f"{ns}tspan")
    assert all("x" in s.attrib for s in spans)


def test_middle_alignment_pushes_the_panel_down(photo):
    a = art.render(photo, cols=40)
    sections = [svg.Section(None, [("K", "v")])]
    top = svg.build(a, sections, theme.get("github-dark"), svg.Layout(panel_align="top"))
    mid = svg.build(a, sections, theme.get("github-dark"), svg.Layout(panel_align="middle"))
    assert top != mid


def test_bad_panel_align_rejected(photo):
    with pytest.raises(ValueError, match="panel_align"):
        svg.build(None, [svg.Section(None, [("K", "v")])], theme.get("github-dark"), svg.Layout(panel_align="sideways"))


# --- theme -----------------------------------------------------------------


def test_theme_override_and_validation():
    base = theme.get("github-dark")
    assert base.merged({"key": "#ff0000"}).key == "#ff0000"
    assert base.merged(None) is base
    with pytest.raises(ValueError, match="unknown theme keys"):
        base.merged({"nonsense": "#000000"})


def test_unknown_theme_rejected():
    with pytest.raises(ValueError, match="unknown theme"):
        theme.get("solarized-eclipse")


# --- github helpers --------------------------------------------------------


def test_templates_substitute_and_leave_unknowns():
    out = gh.apply_templates("{{name}} has {{repos}} repos, {{mystery}}", {"name": "A", "repos": "3"})
    assert out == "A has 3 repos, {{mystery}}"


@pytest.mark.parametrize(
    "since,expected",
    [
        (dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc), "1 month"),
        (dt.datetime(2025, 8, 1, tzinfo=dt.timezone.utc), "1 year"),
        (dt.datetime(2022, 1, 22, tzinfo=dt.timezone.utc), "4 years, 6 months"),
        (dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc), "less than a month"),
    ],
)
def test_age_formatting(since, expected):
    now = dt.datetime(2026, 8, 8, tzinfo=dt.timezone.utc)
    assert gh._humanise_age(since, now) == expected


@pytest.mark.parametrize("n,expected", [(0, "0"), (999, "999"), (1000, "1k"), (1500, "1.5k"), (12300, "12.3k")])
def test_count_formatting(n, expected):
    assert gh._format_count(n) == expected


# --- cli end to end --------------------------------------------------------


def test_init_writes_portable_starter_config(photo, tmp_path):
    cfg_path = tmp_path / "profile" / "termfetch.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "termfetch",
            "init",
            "--user",
            "octocat",
            "--image",
            photo,
            "--theme",
            "dracula",
            "--config",
            str(cfg_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    cfg = json.loads(cfg_path.read_text())
    assert cfg["github"] == "octocat"
    assert cfg["theme"] == "dracula"
    assert not Path(cfg["image"]).is_absolute()
    assert (cfg_path.parent / cfg["image"]).resolve() == Path(photo).resolve()
    assert not set(cfg) - set(cli.DEFAULTS)
    assert "termfetch --config" in result.stdout


def test_init_refuses_to_overwrite_existing_config(tmp_path):
    cfg_path = tmp_path / "termfetch.json"
    cfg_path.write_text("do not replace")
    result = subprocess.run(
        [sys.executable, "-m", "termfetch", "init", "--user", "octocat", "--config", str(cfg_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "--force" in result.stderr
    assert cfg_path.read_text() == "do not replace"


def test_cli_uses_first_run_default_paths(photo, tmp_path, monkeypatch):
    cfg = cli.starter_config("octocat", Path(photo).name)
    (tmp_path / "termfetch.json").write_text(json.dumps(cfg))
    monkeypatch.chdir(tmp_path)

    assert cli.main(["--no-fetch"]) == 0
    out = tmp_path / "termfetch.svg"
    assert out.is_file()
    ET.fromstring(out.read_text())


def test_cli_reports_package_version():
    result = subprocess.run(
        [sys.executable, "-m", "termfetch", "--version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "termfetch 0.2.0"


def test_cli_renders_without_network(photo, tmp_path):
    cfg = {
        "github": "someone",
        "image": photo,
        "imageCols": 20,
        "sections": [{"title": "hi", "fields": [["Name", "{{name}}"], ["Empty", "{{bio}}"]]}],
    }
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))
    out = tmp_path / "card.svg"

    result = subprocess.run(
        [sys.executable, "-m", "termfetch", "--config", str(cfg_path), "--out", str(out), "--no-fetch"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    doc = out.read_text()
    ET.fromstring(doc)
    assert "someone" in doc  # {{name}} falls back to the username
    assert "Empty" not in doc  # row dropped because {{bio}} resolved to nothing


def test_long_values_wrap_onto_aligned_continuation_rows():
    from termfetch.cli import build_sections

    long = "Backend and platform engineer who turns ambiguous customer problems into reliable software"
    cfg = {"valueWrap": 30, "sections": [{"title": None, "fields": [["Bio", long]]}]}
    sections = build_sections(cfg, {})

    fields = sections[0].fields
    assert len(fields) > 1, "expected the value to wrap"
    assert fields[0][0] == "Bio"
    assert all(k == "" for k, _ in fields[1:]), "continuation rows must have an empty key"
    assert all(len(v) <= 30 for _, v in fields)
    # nothing lost or duplicated in the wrap
    assert " ".join(v for _, v in fields) == long


def test_wrapping_is_off_by_default():
    from termfetch.cli import DEFAULTS, build_sections

    long = "x" * 200
    cfg = {**DEFAULTS, "sections": [{"title": None, "fields": [["K", long]]}]}
    assert len(build_sections(cfg, {})[0].fields) == 1


def test_plain_string_field_spans_full_width():
    from termfetch.cli import build_sections

    cfg = {"valueWrap": 0, "sections": [{"title": None, "fields": ["a full width line"]}]}
    key, value = build_sections(cfg, {})[0].fields[0]
    assert key is None and value == "a full width line"


def test_continuation_row_aligns_to_the_value_column():
    doc = svg.build(
        None,
        [svg.Section(None, [("Bio", "first part"), ("", "second part")])],
        theme.get("github-dark"),
        svg.Layout(key_width=10),
    )
    root = ET.fromstring(doc)
    ns = "{http://www.w3.org/2000/svg}"
    xs = [s.attrib["x"] for s in root.iter(f"{ns}tspan") if s.text in ("first part", "second part")]
    assert len(xs) == 2 and xs[0] == xs[1], "wrapped lines must share the value column"


def test_cli_rejects_unknown_config_keys(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({"sections": [{"fields": ["x"]}], "colour": "blue"}))
    result = subprocess.run(
        [sys.executable, "-m", "termfetch", "--config", str(cfg_path), "--out", str(tmp_path / "o.svg")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "unknown config keys" in result.stderr


def test_shipped_example_config_is_valid():
    cfg = json.loads((ROOT / "examples" / "config.json").read_text())
    from termfetch.cli import DEFAULTS

    assert not set(cfg) - set(DEFAULTS)
