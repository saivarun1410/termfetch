# Contributing to termfetch

Thanks for helping improve termfetch. Small, focused pull requests are easiest to review.

## Development setup

```bash
git clone https://github.com/saivarun1410/termfetch
cd termfetch
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

## Before opening a pull request

1. Add or update tests for behaviour changes.
2. Run `pytest -q`.
3. Render the example offline:

   ```bash
   termfetch --config examples/config.json --out /tmp/card.svg --no-fetch
   ```

4. Keep generated files and unrelated formatting changes out of the commit.
5. Explain what changed, why it changed, and how you verified it.

Bug reports and feature requests are welcome in
[GitHub Issues](https://github.com/saivarun1410/termfetch/issues).
