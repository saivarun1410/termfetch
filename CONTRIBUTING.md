# Contributing to Termfetch

Thanks for helping make GitHub profile cards easier to create and maintain.

## Development setup

Termfetch requires Python 3.10 or newer.

```bash
git clone https://github.com/saivarun1410/termfetch.git
cd termfetch
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

## Before opening a pull request

1. Create a focused branch or fork.
2. Add or update tests for behavioural changes.
3. Run `python -m pytest -q`.
4. Render the example offline:

   ```bash
   termfetch --config examples/config.json --out /tmp/card.svg --no-fetch
   ```

5. Regenerate affected example cards when rendering changes.
6. Open a pull request that explains the motivation, user impact, and validation performed.

The default branch is protected. Changes must go through a pull request and satisfy its required
review before merge. Please keep generated assets intentional and avoid committing personal access
tokens, private profile data, virtual environments, or build output.

## Bug reports and feature requests

Open an [issue](https://github.com/saivarun1410/termfetch/issues) with a minimal configuration,
the command you ran, Python version, expected behavior, and actual output. Replace private images
or tokens before attaching files.

## License

By contributing, you agree that your contribution will be licensed under the project's
[MIT License](LICENSE).
