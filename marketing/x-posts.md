# Termfetch X launch copy

The launch post is written to accompany `assets/termfetch-demo.mp4`. Keep the
line breaks. Do not add unrelated hashtags or tag large accounts without a real
reason.

## Launch post

> Your GitHub profile, but make it neofetch.
>
> I built termfetch—a Python CLI that turns your photo + live GitHub stats into a self-contained SVG for your README.
>
> No hosted image service. Six themes. MIT licensed.
>
> https://github.com/saivarun1410/termfetch

## Reply 1 — install

> Install and generate your first card:
>
> `pipx install termfetch`
> `termfetch init --user YOUR_USERNAME --image photo.jpg`
> `termfetch`
>
> Reply with your card. I’ll help the first 10 people configure theirs and repost my favorites.

## Reply 2 — differentiation

> Why a self-contained SVG?
>
> Your README does not depend on an image server at view time. The card stays in a repository you control, and a scheduled GitHub Action can refresh the stats.

## Day 2 — theme gallery

> Same GitHub profile, four terminal moods.
>
> GitHub Dark, Dracula, Nord or GitHub Light—which one would you put in your README?
>
> termfetch includes six themes and supports custom colors.
>
> https://github.com/saivarun1410/termfetch

Attach `assets/theme-gallery.png` and reply to every choice with one useful customization tip.

## Day 3 — technical story

> A GitHub README SVG cannot rely on a webfont.
>
> termfetch positions every terminal glyph explicitly so ASCII columns do not drift when different operating systems choose different monospace fonts.
>
> Small implementation detail. Much more reliable card.

## Day 4 — community showcase template

> The best part of releasing termfetch: seeing someone else’s profile become terminal art.
>
> Here is [NAME]’s card in [THEME].
>
> Want help making yours? Reply with your GitHub username.

Get permission before attaching the card and tag the creator.

## Day 5 — feature poll

> What should termfetch improve next?
>
> 1. More themes
> 2. Easier image cropping
> 3. More GitHub stats
> 4. A browser-based config preview

Use X's native poll when available and turn the winning answer into a public issue.

## Day 6 — before and after

> A profile README can be useful and still feel personal.
>
> Before: a wall of badges.
> After: one self-contained terminal card generated from your photo and GitHub data.
>
> Built with termfetch: https://github.com/saivarun1410/termfetch

## Day 7 — transparent recap template

> One week since I released termfetch:
>
> • [USERS] people tried it
> • [CARDS] cards shared
> • [STARS] GitHub stars
> • [ISSUES] useful issues opened
>
> Thank you to everyone who tested it. Next I’m working on [FEATURE].

Use real numbers, including small ones.

## Useful reply bank

**Does it upload my photo?**

> No. Rendering happens locally and the output is a static SVG. You decide whether to commit that SVG to your profile repository.

**Will the stats update automatically?**

> The repository includes a scheduled GitHub Actions example that can regenerate and commit the card for you.

**Can I use a logo instead of a photo?**

> Yes. Logos work particularly well with the ASCII and blocks character sets.

**How can I help?**

> Try it on your own profile, share the result, and open an issue if anything in the first-run experience is confusing. Contributions are welcome through pull requests.

## Show HN

**Title:**

> Show HN: Termfetch – turn a GitHub profile into a neofetch-style SVG card

**Text:**

> I built Termfetch, a Python CLI that combines a photo or logo with public GitHub statistics and renders the result as a self-contained SVG for a profile README. The card does not call an image service when viewed; it lives in the user's repository and can be refreshed with a scheduled GitHub Action. It supports six themes and several ASCII/block rendering modes. I would especially value feedback on the first-run configuration and SVG portability.

## Reddit or developer-community post

**Title:**

> I built an MIT-licensed CLI that turns a GitHub profile into a neofetch-style SVG

**Body:**

> Termfetch takes a local photo or logo, combines it with public GitHub statistics, and renders one self-contained SVG for a profile README. It is installable with `pipx install termfetch`, has six themes, and includes a GitHub Actions example for scheduled refreshes. I am looking for honest feedback on setup, image cropping, and which statistics are actually useful—not just stars.
>
> Repository: https://github.com/saivarun1410/termfetch
