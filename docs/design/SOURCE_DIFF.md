# `_source/` vs `app/` — Integration Diff

The folder [`Redisign app/_source/`](../../Redisign%20app/_source/) is a
snapshot of the Python/PySide codebase bundled with the HTML prototype. Per
`redisign_roadmap.md` §1, it is **byte-identical to `app/` modulo CRLF line
endings** — the snapshot was exported from a Windows workstation and the live
tree uses LF on some files.

## Status

- **Verdict**: CRLF-only differences. No source change required from
  `_source/`; it is a redundant copy used only to pair the HTML prototype with
  a reproducible Python tree at the time of handoff.
- **Scope for this redesign**: `_source/` is **excluded** from every sprint.
  Integration work happens under `app/` only.

## Rule

Do not edit, import, or reference `_source/` from production code. Delete-on-
sight if it drifts. The HTML file in the same folder remains the visual
source of truth.
