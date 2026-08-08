"""Fetch the GitHub numbers used to fill in template variables.

Only the standard library is used, so the package's single hard dependency stays Pillow.
A token is optional: without one you get the unauthenticated REST rate limit (60
requests/hour per IP), which is plenty for a card that regenerates a few times a day.
"""

from __future__ import annotations

import datetime as dt
import json
import urllib.error
import urllib.request

API = "https://api.github.com"
UA = "termfetch (+https://github.com/saivarun1410/termfetch)"


class GitHubError(RuntimeError):
    pass


def _get(url: str, token: str | None) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:200]
        raise GitHubError(f"GET {url} failed: {exc.code} {detail}") from None
    except urllib.error.URLError as exc:
        raise GitHubError(f"GET {url} failed: {exc.reason}") from None


def _humanise_age(since: dt.datetime, now: dt.datetime) -> str:
    months = (now.year - since.year) * 12 + (now.month - since.month)
    if now.day < since.day:
        months -= 1
    years, months = divmod(max(months, 0), 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    return ", ".join(parts) or "less than a month"


def _format_count(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


def fetch(
    username: str,
    token: str | None = None,
    top_languages: int = 5,
    language_mode: str = "repos",
    now: dt.datetime | None = None,
) -> dict[str, str]:
    """Return template variables for ``username``.

    ``language_mode`` picks how languages are ranked. ``"repos"`` counts how many
    repositories name each language as their primary one — a single API call.
    ``"bytes"`` sums the actual bytes written in each language, which is more
    representative but costs one extra call per repository.
    """
    if language_mode not in ("repos", "bytes"):
        raise ValueError(f"language_mode must be 'repos' or 'bytes', got {language_mode!r}")
    now = now or dt.datetime.now(dt.timezone.utc)
    user = _get(f"{API}/users/{username}", token)
    if not isinstance(user, dict):
        raise GitHubError("unexpected response shape for user")

    repos: list[dict] = []
    page = 1
    while page <= 10:  # 1000 repos is far past the point of diminishing returns
        batch = _get(f"{API}/users/{username}/repos?per_page=100&page={page}&type=owner", token)
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    own = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in own)
    forks = sum(r.get("forks_count", 0) for r in own)

    counts: dict[str, int] = {}
    if language_mode == "bytes":
        for r in own:
            try:
                per_repo = _get(f"{API}/repos/{username}/{r['name']}/languages", token)
            except GitHubError:
                continue  # one unreadable repo shouldn't sink the whole card
            if isinstance(per_repo, dict):
                for lang, size in per_repo.items():
                    counts[lang] = counts.get(lang, 0) + int(size)
    else:
        for r in own:
            lang = r.get("language")
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
    languages = ", ".join(sorted(counts, key=lambda k: (-counts[k], k))[:top_languages])

    created = dt.datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))

    return {
        "username": user.get("login") or username,
        "name": user.get("name") or user.get("login") or username,
        "bio": (user.get("bio") or "").replace("\r\n", " ").replace("\n", " ").strip(),
        "location": user.get("location") or "",
        "company": user.get("company") or "",
        "blog": user.get("blog") or "",
        "followers": _format_count(user.get("followers", 0)),
        "following": _format_count(user.get("following", 0)),
        "repos": _format_count(len(own)),
        "public_repos": _format_count(user.get("public_repos", 0)),
        "stars": _format_count(stars),
        "forks": _format_count(forks),
        "languages": languages,
        "created": created.date().isoformat(),
        "uptime": _humanise_age(created, now),
        "today": now.date().isoformat(),
    }


def apply_templates(text: str, variables: dict[str, str]) -> str:
    """Substitute ``{{name}}`` style placeholders. Unknown names are left as-is."""
    for key, value in variables.items():
        text = text.replace("{{" + key + "}}", value)
    return text
