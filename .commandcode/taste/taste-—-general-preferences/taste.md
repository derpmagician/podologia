# Taste — general preferences
- Communicates in Spanish and expects the agent to work and respond in Spanish (code comments, docstrings, README, UI strings). Confidence: 0.9
- Prefers a minimal project root: the entry HTML (index.html) is the only file that belongs at the root, with all code, assets, and scripts organized into a subfolder. Confidence: 0.6
- Before a large refactor, wants an upfront pass that explains the purpose of each existing file and proposes a software architecture to bring order, rather than an immediate edit. Confidence: 0.5
- Runs the code himself and expects claimed changes to actually work end-to-end: verification must exercise the real program (real browser, real HTTP requests, real database), not just per-file static/syntax checks. Confidence: 0.6
- Wants the project to be portable across machines: scripts/config must not hardcode absolute, machine-specific paths (e.g. DB file paths) — resolve such locations from the environment instead. Confidence: 0.7
- Wants the app to bootstrap itself on a clean machine with no manual setup step: it should provision missing infrastructure (e.g. create the database, connecting to master first) automatically on startup instead of requiring the user to run a script by hand. Confidence: 0.6
