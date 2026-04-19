# FC26 Analytics — UI/UX Redesign Integration Roadmap

## 1) Summary of the Redesign Approach

The reference design lives in [Redisign app/FC26 Analytics Redesign.html](Redisign%20app/FC26%20Analytics%20Redesign.html). The `_source/` folder is a snapshot of the **current** Python/PySide codebase (byte-identical to [app/](app/) modulo CRLF line endings) — it is the **integration skeleton**, not new code. The HTML prototype is the **visual and interaction target**.

Key characteristics of the target design:

- **Shell**: sticky sidebar (collapsible, `232px → 60px`) + topbar (breadcrumb, global search, date chip, theme toggle, primary CTA) + content + footer status bar.
- **Theming**: CSS custom-properties style token system (`--bg`, `--panel`, `--line`, `--accent`, `--ok/warn/bad`, mono/sans/display fonts, `--radius`, `--pad`, density multiplier). Dark + light variants, three density modes.
- **Primitives**: `card`, `chip` (ok/warn/bad/accent/mono), `btn` (primary/ghost/sm), `icon-btn`, `pill-num`, `pos-badge`, `avatar`, `section-title`, `tab-row/tab`, `filter`, `dropzone`, `log`, `legend`, `statusbar`.
- **Page-specific widgets**: `hero` with radial gradients + crest + form dots, `kpi-grid` (6-col with feature tile + sparkline), `scatter`, `line-chart` SVG, `pitch` with positioned players, `bars`, `dial` (conic-gradient ring), `drawer` (attribute rows with mini-bars), `file-row`, `tweaks` panel.
- **Typography hierarchy**: 10px labels (uppercase, tracked), 11–13px body, 22px section titles, 26–56px KPIs/hero — current theme only emits 11/13/15/20px and no display font, no mono font.
- **Color depth**: the HTML uses two panel tones (`panel`, `panel-2`), two line tones, `color-mix()`-tinted chips, gradient fills on bars/crests. Current [app/ui/theme.py](app/ui/theme.py) has a single `surface` + `surface_alt` and no gradients, no tint system.

### Gap summary (current vs. target)

| Area | Current ([app/ui](app/ui/)) | Target (HTML) | Gap |
|---|---|---|---|
| Shell | `QMainWindow` + `QListWidget` nav | Sidebar w/ brand, sections, badges, footer career-card, collapse toggle + topbar w/ search + breadcrumb + status bar | **Major** |
| Theme tokens | 4 spacing, 3 radii, 4 font sizes, 8 colors | +display/mono families, +panel-2/line-2, +ok/warn/bad tinted variants, density multiplier, light-theme swap | **Major** |
| Primitives | `QFrame#card`, QSS for QPushButton/QTableView | Chips, pills, pos-badges, icon-btn, tabs, filters, legend | **Major** |
| Overview | Basic cards | Hero + 6-col KPI grid w/ sparklines | **Rewrite** |
| Squad/Wonderkids | Table + sidebar | Table + **right drawer** w/ attribute bars | **Major** |
| Tactics | TBD per [app/ui/pages/tactics_page.py](app/ui/pages/tactics_page.py) | Pitch view with positioned players + formation bars | **Major** |
| Transfers | Table | Scatter (age × value) + table + deal log | **Major** |
| Import | Dropzone (recent commit f2f71c8) | Dropzone + file rows w/ OK/Partial/Error states + streaming log | **Refine** |
| Charts | `chart_panel.py`, `sparkline.py` | Styled SVG lines, scatter grid, conic dials, gradient bars | **Restyle** |
| UX states | Minimal | Loading / empty / error + density + theme toggle + tweaks panel | **New** |

---

## 2) Technical-Plan Additions

See **§17 UI Architecture v2** in [PLAN_TECHNIQUE.md](PLAN_TECHNIQUE.md) for the authoritative technical-plan extension. Summary:

1. **Design-token layer** (`app/ui/design/tokens.py`): palette (dark/light), typography, spacing, radii, density multipliers, elevation, motion.
2. **QSS builder** (`app/ui/design/qss.py`): `build_qss(theme, density)` composing base + primitives + components.
3. **Component library** (`app/ui/components/`): Chip, Pill, PosBadge, Avatar, IconButton, PrimaryButton, GhostButton, Tabs, FilterChip, SectionTitle, DrawerPanel, Dropzone, LogView, StatusBar, Tweaks.
4. **Shell layer** (`app/ui/shell/`): Sidebar, Topbar, AppShell.
5. **Chart primitives** (`app/ui/charts/`): line_chart, scatter, pitch, dial, bar_row.
6. **State conventions**: each page exposes `set_state("loading" | "empty" | "error" | "ready")`.
7. **Theme-switching contract**: `ThemeManager` signals `theme_changed(Palette)`; widgets re-polish without reinstantiating.

Design-system rules enforced across sprints:
- Colors via tokens only — no string literals in widgets.
- Spacing via `Spacing` tokens — no magic pixels.
- Object names follow HTML convention (`card`, `kpi`, `chip--ok`, `btn--primary`) so QSS maps 1:1.
- Fonts declared once in `QApplication` (Inter + JetBrains Mono embedded under `packaging/fonts/`).
- No business logic in UI components; pages are glue only.

---

## 3) Full Redesign Roadmap

### Phase 0 — Foundation & Asset Preparation (MANDATORY) — **COMPLETED**

**Sprint 0.1 — Asset intake & audit**
- Objectives: confirm scope, lock the HTML as the visual source of truth.
- Tasks:
  - Freeze [Redisign app/FC26 Analytics Redesign.html](Redisign%20app/FC26%20Analytics%20Redesign.html) (read-only).
  - Extract token table (colors, spacing, radii, fonts, density) to `docs/design/TOKENS.md`.
  - Screenshot each page/state from the HTML → `docs/design/screens/`.
  - Diff `_source/` vs. `app/` (confirmed: CRLF-only); exclude `_source/` from integration targets.
- Output: TOKENS.md, per-page screenshot catalog, signed-off inventory list.

**Sprint 0.2 — Design-system scaffolding (no visual change yet)**
- Objectives: create the empty scaffold so later sprints have a home.
- Tasks:
  - Create `app/ui/design/`, `app/ui/components/`, `app/ui/shell/`, `app/ui/charts/` packages with `__init__.py` only.
  - Add Inter + JetBrains Mono under `packaging/fonts/`; register in `app/main.py` via `QFontDatabase`.
  - Introduce `ThemeManager` singleton in `app/ui/design/theme_manager.py` (mirrors current `load_qss` behavior to avoid regression).
  - Add `tests/ui/smoke_test_shell.py` that boots the app and asserts QSS loads.
- Output: compiles, runs, looks identical to today.

**Sprint 0.3 — Page-level state contract**
- Objectives: ensure later migrations can swap visuals without touching data flow.
- Tasks:
  - Extend [app/ui/pages/_base.py](app/ui/pages/_base.py) with `set_state(state: Literal[...])` and default loading/empty/error views.
  - Retrofit each existing page to call `set_state` at current data-ready points (no visual change — default stack = current widget).
- Output: every page emits explicit states.

---

### Phase 1 — Design Tokens & Theming System — **COMPLETED**

**Sprint 1.1 — Token model**
- Port HTML `:root` variables into `app/ui/design/tokens.py`: `Palette(dark|light)`, `Typography`, `Spacing`, `Radii`, `Elevation`, `Density`.
- Keep public API of [app/ui/theme.py](app/ui/theme.py) as a thin shim → forwards to new module (no breaking imports).

**Sprint 1.2 — QSS builder**
- Implement `build_qss(theme, density)` composing base + primitives + components.
- Switch `QApplication.setStyleSheet` to builder output.
- Add visual regression snapshot tests (Qt `QPixmap` compare) for 2 screens.

**Sprint 1.3 — Theme & density switching**
- Wire a theme toggle (dark/light) + density selector into an internal dev-only debug panel.
- Verify re-polish on all open widgets without restart.
- Output: working theme toggle; public UI unchanged.

---

### Phase 2 — Shell Redesign (Sidebar + Topbar + Statusbar) — **COMPLETED**

**Sprint 2.1 — Sidebar**
- Build `Sidebar` widget: brand block, section titles, `NavItem` (icon + label + badge + active-bar), footer `CareerCard`, collapse toggle.
- Replace current `QListWidget` nav in [app/ui/app_window.py](app/ui/app_window.py) behind a feature flag.
- Icons: inline SVG → `QIcon` via `QSvgRenderer` into `QPixmap` at runtime (no asset pipeline needed).

**Sprint 2.2 — Topbar & Statusbar**
- Build `Topbar`: breadcrumb (bound to current page title), search (`⌘K` stub, no behavior yet), date chip, theme toggle, "Import snapshot" primary CTA wired to existing import flow.
- Build `StatusBar` bottom bar (cache state, row counts, build hash).

**Sprint 2.3 — Shell assembly & flag flip**
- `AppShell` composes Sidebar + Topbar + page stack + StatusBar.
- Flip the feature flag; delete legacy chrome.

---

### Phase 3 — Component Library Buildout

**Sprint 3.1 — Core primitives**
- `Chip` (variants: default/ok/warn/bad/accent/mono), `Pill` (hi/md/lo), `PosBadge` (GK/DEF/MID/ATT), `Avatar`.

**Sprint 3.2 — Interactive controls**
- `PrimaryButton`, `GhostButton`, `IconButton`, `FilterChip`, `Tabs`, `SectionTitle`.

**Sprint 3.3 — Layout primitives**
- Styled `Card` (head/body/no-pad), `TwoCol`, `ThreeCol`, `FourCol` layout helpers, `Legend`.

**Sprint 3.4 — Heavy components**
- `DrawerPanel` (right-side, collapsible, attribute-row with mini-bars).
- `Dropzone` (drag-hover states, file-row list, status pills).
- `LogView` (mono, colorized ts/ok/warn/err lines).

---

### Phase 4 — Chart Redesign

**Sprint 4.1 — Sparkline & line chart**
- Upgrade [app/ui/widgets/sparkline.py](app/ui/widgets/sparkline.py) to match HTML sparkline (token colors, smoothed polyline).
- Build `LineChart` (QtCharts or custom `QPainter`) with gridlines, axis, hover tooltip — token-driven styling.

**Sprint 4.2 — Scatter & bars**
- `ScatterChart` with quadrant grid (matches HTML `.scatter` background).
- `BarRow` (label / gradient track / value, variants ok/warn/accent).

**Sprint 4.3 — Dial & pitch**
- `Dial` (conic-gradient ring via `QPainter.drawArc`).
- `Pitch` widget: SVG pitch background + positioned player tokens (absolute-positioned children).

**Sprint 4.4 — Chart integration**
- Replace chart usages in existing pages' `chart_panel.py` with the new primitives. No data changes.

---

### Phase 5 — Page-by-Page Redesign

**Sprint 5.1 — Overview**
- Port hero card (crest, title, form dots, league position).
- 6-col KPI grid with feature tile + sparklines.
- Keep data binding from existing [app/ui/pages/overview_page.py](app/ui/pages/overview_page.py).

**Sprint 5.2 — Import**
- Dropzone + file-row list + log stream bound to existing [app/import_/](app/import_/) pipeline events.
- Preserve multi-file behavior added in commit 9ee855e.

**Sprint 5.3 — Squad**
- `DataTable` with pos-badge, pill-num, avatar, name-cell.
- Right `DrawerPanel` wired to row selection showing player attributes.

**Sprint 5.4 — Wonderkids**
- Filters bar (age, position, potential bands).
- Table + drawer reusing Squad components; page-specific scoring column styling only.

**Sprint 5.5 — Tactics**
- Pitch component + formation-load bars + dials for tactical metrics.

**Sprint 5.6 — Transfers**
- Scatter (age × value), transfer table, deals log; reuse Phase-4 primitives.

**Sprint 5.7 — Analytics (standings + cross-cutting)**
- Port analytics page last — it aggregates widgets built in prior sprints.

---

### Phase 6 — UX Polish & Hardening

**Sprint 6.1 — States**
- Wire real `loading / empty / error` rendering on every page (Phase-0 contract).
- Add toasts/notifications (bottom-right) using status colors.

**Sprint 6.2 — Navigation & focus**
- Keyboard shortcuts (`⌘1..7` for pages, `⌘K` search, `⌘B` sidebar collapse).
- Focus rings styled via QSS `:focus`.

**Sprint 6.3 — Visual QA**
- Side-by-side comparison vs. HTML for every page at dark+light × compact+cozy+comfortable.
- Pixel-diff snapshot tests for 8 canonical screens.

**Sprint 6.4 — Performance**
- Ensure QSS recomputes only on theme change; verify no per-frame allocations in custom-painted widgets.
- Profile startup; keep under current baseline.

---

## 4) Migration Strategy

**Principle: non-breaking, incremental, flag-guarded.**

1. **Parallel namespaces.** New code lands under `app/ui/design/`, `app/ui/components/`, `app/ui/shell/`, `app/ui/charts/`. The existing `app/ui/widgets/` and `app/ui/pages/` modules are **not deleted** until their replacements are wired and green.
2. **Shim old theme API.** [app/ui/theme.py](app/ui/theme.py) becomes a forwarding shim over `app/ui/design/`, so existing imports (`from app.ui.theme import Palette, load_qss`) keep working across phases.
3. **Feature flag for shell.** Phase 2 ships behind `FC26_UI_V2=1`. Dev flips it; once stable, the flag is removed and legacy chrome deleted in a single commit.
4. **One page at a time.** Phase 5 migrates pages individually. Each page keeps its existing data-loading code; only the view layer changes. The page's public signature (`__init__`, `load_data`, `set_state`) stays stable so `app_window.py` doesn't care.
5. **Separation of UI from logic.** No sprint touches [app/analytics/](app/analytics/), [app/domain/](app/domain/), [app/services/](app/services/), [app/import_/](app/import_/), or [app/core/](app/core/). If a page currently mixes logic into the widget, the sprint **extracts** logic into a `services/` module first as a prep step, then redesigns the view — never both at once.
6. **Rollback anchor per sprint.** Every sprint ends at a green build with a tagged commit; any sprint can be reverted without orphaning others.
7. **Smoke + snapshot tests gate each sprint.** `tests/ui/` grows as components ship; CI runs the smoke boot.

---

## Cross-Sprint Rules

1. **No business-logic changes.** UI-only. Do not modify files under [app/analytics/](app/analytics/), [app/domain/](app/domain/), [app/services/](app/services/), [app/import_/](app/import_/), [app/core/](app/core/), [app/config/](app/config/) unless the sprint explicitly calls for an *extraction* from a view.
2. **Respect existing architecture.** `main.py` → `AppShell` → pages → widgets. Pages stay thin; logic lives in services.
3. **Tokens only.** No hex codes, no magic pixels inside widgets — everything comes from `tokens.py`.
4. **Object-name contract.** Widgets set `setObjectName(...)` matching the HTML class (`"card"`, `"kpi"`, `"chip--ok"`); styling lives in QSS, not in `setStyleSheet` on instances.
5. **No regressions.** Smoke boot + existing analytics unit tests ([tests/](tests/)) must stay green at the end of every sprint.
6. **Visual consistency.** Every new component renders correctly in dark + light and in all three densities before the sprint is marked done.
7. **Realism for PySide.** Effects that CSS provides for free (`color-mix`, `backdrop-filter`, conic gradients, `-webkit-background-clip: text`) are approximated via `QPainter`/`QLinearGradient`/pre-blended tokens. No web-only effect blocks a sprint; document approximations in `docs/design/APPROXIMATIONS.md`.
8. **No new features.** Redesign ≠ feature work. Anything beyond visual parity is logged as follow-up, not done inline.
9. **Commit hygiene.** One sprint = one reviewable branch, rebased on `main`, with screenshots in the PR.
