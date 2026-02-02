# Contributing

Thank you for considering contributing to BiasGuard! We welcome contributions of all kinds.

## How to Contribute

- **Bug Reports:** If you find a bug or have a feature request, please open an issue. Describe the problem or suggestion clearly and include steps to reproduce, if applicable.
- **Pull Requests:** Fork the repository and create a new branch for your changes. Follow our coding standards and make sure tests pass locally before submitting your PR. Provide a clear description of the changes and reference any related issues.

## Development Setup

To install dependencies and run tests locally:

```bash
python -m pip install -e .[dev]
pytest -q
ruff check .
```

We use [ruff](https://ruff.rs/) for linting and [pytest](https://pytest.org/) for testing. Make sure your code is formatted and passes the linter before submitting.

## Code Style

- Use descriptive variable and function names.
- Write docstrings for public functions and classes.
- Keep functions short and focused; break complex logic into smaller functions where possible.
- Avoid using em dashes (—); use parentheses or commas to separate phrases.

## Commit Messages

- Use the imperative mood in the subject line (e.g., "Add new metric" not "Added new metric").
- Limit the subject line to 50 characters; the body should provide additional context.

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.
