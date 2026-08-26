# Contributing

Keep contributions small, deterministic, and easy to inspect.

1. Read [AGENTS.md](AGENTS.md) and [docs/SCOPE.md](docs/SCOPE.md).
2. Keep the dependency direction `demo -> phemacast-lite -> prompits-lite`.
3. Add tests for every contract or workflow change.
4. Use deterministic provider doubles only in tests. Runtime financial data must
   come through the yfinance adapter, with no fixture or synthetic fallback.
5. Run `python -m pytest` and the compile check before opening a pull request.

Bug reports should include the Python version, exact command, expected result,
and the smallest reproducible input. Never include passwords, API keys, tokens,
or proprietary datasets.
