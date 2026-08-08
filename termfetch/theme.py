"""Colour schemes for the generated card."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Theme:
    background: str
    title: str
    key: str
    value: str
    separator: str
    border: str
    chrome: str  # title-bar strip behind the window buttons
    mono: str  # colour used when the art is rendered without colour

    def merged(self, overrides: dict[str, str] | None) -> "Theme":
        if not overrides:
            return self
        unknown = set(overrides) - {f for f in self.__dataclass_fields__}
        if unknown:
            raise ValueError(f"unknown theme keys: {sorted(unknown)}")
        return replace(self, **overrides)


THEMES: dict[str, Theme] = {
    "github-dark": Theme(
        background="#0d1117",
        title="#58a6ff",
        key="#3fb950",
        value="#c9d1d9",
        separator="#4d5560",
        border="#30363d",
        chrome="#161b22",
        mono="#c9d1d9",
    ),
    "github-light": Theme(
        background="#ffffff",
        title="#0969da",
        key="#1a7f37",
        value="#1f2328",
        separator="#d1d9e0",
        border="#d1d9e0",
        chrome="#f6f8fa",
        mono="#1f2328",
    ),
    "dracula": Theme(
        background="#282a36",
        title="#bd93f9",
        key="#50fa7b",
        value="#f8f8f2",
        separator="#44475a",
        border="#44475a",
        chrome="#21222c",
        mono="#f8f8f2",
    ),
    "gruvbox": Theme(
        background="#282828",
        title="#fabd2f",
        key="#b8bb26",
        value="#ebdbb2",
        separator="#504945",
        border="#504945",
        chrome="#1d2021",
        mono="#ebdbb2",
    ),
    "nord": Theme(
        background="#2e3440",
        title="#88c0d0",
        key="#a3be8c",
        value="#eceff4",
        separator="#434c5e",
        border="#434c5e",
        chrome="#3b4252",
        mono="#eceff4",
    ),
    "tokyo-night": Theme(
        background="#1a1b26",
        title="#7aa2f7",
        key="#9ece6a",
        value="#c0caf5",
        separator="#292e42",
        border="#292e42",
        chrome="#16161e",
        mono="#c0caf5",
    ),
}


def get(name: str) -> Theme:
    try:
        return THEMES[name]
    except KeyError:
        raise ValueError(f"unknown theme {name!r}; expected one of {sorted(THEMES)}") from None
