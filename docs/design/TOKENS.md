# Design Tokens — FC26 Analytics Redesign

Extracted from the frozen HTML prototype [`Redisign app/FC26 Analytics Redesign.html`](../../Redisign%20app/FC26%20Analytics%20Redesign.html) (`:root` and `html[data-theme="light"]` blocks at lines 8–45).

This document is the authoritative token table consumed by Phase 1 (`app/ui/design/tokens.py`). No color literal may appear outside `tokens.py`; no magic pixel may appear outside the spacing/radii tables.

---

## 1. Palette

### 1.1 Dark (default)

| Token       | Value     | Usage                                              |
|-------------|-----------|----------------------------------------------------|
| `bg`        | `#0b0d12` | Application background, main canvas                |
| `panel`     | `#11141b` | Card, sidebar, topbar, statusbar surface           |
| `panel_2`   | `#161a23` | Nested panel, table header, hover surface          |
| `line`      | `#1f2430` | Default border, divider                            |
| `line_2`    | `#262c3a` | Emphasized border (hover, active, drawer split)    |
| `text`      | `#e7eaf2` | Primary foreground                                 |
| `muted`     | `#8891a4` | Secondary text, labels                             |
| `dim`       | `#5b6378` | Tertiary text, disabled                            |
| `accent`    | `#7c9cff` | Primary accent, active nav bar, primary CTA        |
| `accent_2`  | `#a7b8ff` | Accent hover, gradient terminus                    |
| `ok`        | `#5ad19a` | Success pill, positive chip, OK status             |
| `warn`      | `#f3c969` | Warning pill, partial status                       |
| `bad`       | `#ef6f6f` | Danger pill, error status                          |
| `chip`      | `#1a1f2a` | Chip background (default variant)                  |

### 1.2 Light

| Token       | Value     | Notes                                              |
|-------------|-----------|----------------------------------------------------|
| `bg`        | `#f3f4f8` |                                                    |
| `panel`     | `#ffffff` |                                                    |
| `panel_2`   | `#f7f8fc` |                                                    |
| `line`      | `#e3e6ee` |                                                    |
| `line_2`    | `#d9dde8` |                                                    |
| `text`      | `#121521` |                                                    |
| `muted`     | `#5b6376` |                                                    |
| `dim`       | `#8690a4` |                                                    |
| `chip`      | `#eef1f7` |                                                    |
| `accent`    | `#3858d4` |                                                    |
| `accent_2`  | `#6a86ea` |                                                    |
| `ok/warn/bad` | *inherits dark* | HTML prototype does not override; reuse dark values. |

---

## 2. Typography

Three families, seven sizes. Family literals mirror the HTML `--sans / --mono / --display` declarations.

| Token       | Value                                                         |
|-------------|---------------------------------------------------------------|
| `sans`      | `"Inter", "Segoe UI", system-ui, sans-serif`                  |
| `mono`      | `ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas`  |
| `display`   | `"Inter", system-ui, sans-serif`                              |

| Size | Name     | Usage                                               |
|------|----------|-----------------------------------------------------|
| 10   | `xs`     | Uppercase tracked labels (section kicker, legend)   |
| 11   | `sm`     | Muted meta, chip text                               |
| 13   | `base`   | Body                                                |
| 15   | `md`     | Emphasized body, nav label                          |
| 22   | `lg`     | Section title                                       |
| 26   | `xl`     | KPI value                                           |
| 56   | `hero`   | Hero tile number                                    |

Current `app/ui/theme.py` emits only `11/13/15/20` and a single family — gap documented in `redisign_roadmap.md` §1.

---

## 3. Spacing

Base unit `--pad: 16px` in HTML. The scale below is the one `app/ui/theme.py` already uses and matches HTML usage:

| Token | px |
|-------|----|
| `xs`  | 4  |
| `sm`  | 8  |
| `md`  | 12 |
| `lg`  | 16 |
| `xl`  | 24 |
| `xxl` | 32 |

---

## 4. Radii

| Token | px | HTML var          |
|-------|----|-------------------|
| `sm`  | 6  | `--radius-sm`     |
| `md`  | 10 | `--radius`        |
| `lg`  | 14 | implicit (drawer) |

---

## 5. Density

Prototype exposes three density modes via `html[data-density]`:

| Mode          | `--pad` | multiplier |
|---------------|---------|------------|
| `compact`     | `10px`  | `0.85`     |
| `cozy`        | `16px`  | `1.00` (default) |
| `comfortable` | `20px`  | `1.15`     |

Applied uniformly to paddings; font sizes are unaffected.

---

## 6. Shell geometry

| Token   | Value (expanded) | Value (collapsed)         |
|---------|------------------|---------------------------|
| `sb-w`  | `232px`          | `60px` (`data-sidebar="collapsed"`) |

---

## 7. Elevation & motion

HTML uses only two raised surfaces: the right `drawer` and the `tweaks` panel. No explicit `box-shadow` token is declared at `:root`; document concrete blurred shadows during Phase 1 QSS implementation. Motion: default CSS transitions (`.15s / .2s ease`) for hover, theme, density swaps.

---

## 8. Status pills & chip variants

Derived from the existing palette via `color-mix()` in HTML:

| Variant | Background                               | Foreground |
|---------|------------------------------------------|------------|
| default | `chip`                                   | `text`     |
| ok      | `color-mix(in srgb, ok 18%, chip)`       | `ok`       |
| warn    | `color-mix(in srgb, warn 18%, chip)`     | `warn`     |
| bad     | `color-mix(in srgb, bad 18%, chip)`      | `bad`      |
| accent  | `color-mix(in srgb, accent 18%, chip)`   | `accent`   |
| mono    | `chip`                                   | `muted` (font `mono`) |

PySide has no `color-mix()`; Phase 1 must pre-blend the tinted values and expose them as `palette.chip_ok`, `palette.chip_warn`, … (see `PLAN_TECHNIQUE.md` §17.7).

---

## 9. Provenance

| Source                                                                                                                 | Lines    |
|------------------------------------------------------------------------------------------------------------------------|----------|
| [`Redisign app/FC26 Analytics Redesign.html`](../../Redisign%20app/FC26%20Analytics%20Redesign.html) — `:root`         | 8–30     |
| same — `html[data-theme="light"]`                                                                                      | 32–43    |
| same — density variants                                                                                                | 45–46    |
| same — sidebar collapsed                                                                                               | 54       |
