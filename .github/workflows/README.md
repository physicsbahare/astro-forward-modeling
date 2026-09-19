# Active GitHub Actions

The repository used to contain many one-off Gate-B/Gate-C/Gate-D experimental workflow files. Those experiments are preserved in git history and their scientific receipts remain under `benchmarks/`, but keeping every historical workflow active made the repository difficult to navigate.

The active workflow directory is intentionally limited to:

- `verification.yml` - lightweight regression/verification suite.
- `passive-spiral-p1.yml` - controlled spiral-feature survival test.
- `passive-spiral-p2-real-context.yml`
- `passive-spiral-p3-phase-null.yml`
- `passive-spiral-p4-mask-control.yml`
- `passive-spiral-p5-robust-loss.yml`

The current GOLD403 Lenstronomy/Galight validation is primarily a local-data workflow because the large COSMOS-Web products and private/local catalog inputs are not committed to GitHub.

Historical workflow definitions can be recovered from git history if a benchmark must be rerun.
