# Embedded Fonts

The redesign targets the typography stack declared in the HTML prototype:

- **Sans / Display** — Inter Variable (`Inter-Variable.ttf`)
- **Mono** — JetBrains Mono Variable (`JetBrainsMono-Variable.ttf`)

Drop the two `.ttf` files in this directory. `app/main.py` registers them at
startup via `QFontDatabase.addApplicationFont`. If the files are missing, the
application falls back to the OS stack declared in `docs/design/TOKENS.md`
(`Segoe UI` / `Consolas` on Windows) — the prototype was designed to degrade
gracefully.

Both fonts are released under the SIL Open Font License 1.1. Source:

- Inter — https://github.com/rsms/inter
- JetBrains Mono — https://github.com/JetBrains/JetBrainsMono

The actual font binaries are **not committed**; check them in via the release
pipeline or download at build time. See `packaging/build.ps1`.
