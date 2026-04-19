# Screen Catalog — FC26 Analytics Redesign

Reference inventory of every screen/state exposed by the HTML prototype at
[`Redisign app/FC26 Analytics Redesign.html`](../../../Redisign%20app/FC26%20Analytics%20Redesign.html).
Open the HTML in a browser, switch to the target page via the sidebar, and
capture a PNG at 1440×900 into this directory using the filename in the
**Capture** column. All images are referenced by later sprints as the visual
source of truth for pixel-diff tests.

The capture is a manual step — the prototype is a single self-contained HTML
file with no asset pipeline, so no scripted renderer is required.

## Pages

| Page       | Section id in HTML         | Capture filename              |
|------------|----------------------------|-------------------------------|
| Overview   | `page-overview`            | `overview-dark.png`           |
| Analytics  | `page-analytics`           | `analytics-dark.png`          |
| Squad      | `page-squad`               | `squad-dark.png`              |
| Wonderkids | `page-wonderkids`          | `wonderkids-dark.png`         |
| Tactics    | `page-tactics`             | `tactics-dark.png`            |
| Transfers  | `page-transfers`           | `transfers-dark.png`          |
| Import     | `page-import`              | `import-dark.png`             |

## Cross-cutting states

| State             | How to reach                                            | Capture filename          |
|-------------------|---------------------------------------------------------|---------------------------|
| Light theme       | Tweaks panel → theme toggle                             | `*-light.png` (per page)  |
| Sidebar collapsed | Sidebar chevron                                         | `shell-collapsed.png`     |
| Compact density   | Tweaks panel → density `compact`                        | `shell-compact.png`       |
| Comfortable density | Tweaks panel → density `comfortable`                  | `shell-comfortable.png`   |
| Drawer open       | Squad → click any table row                             | `squad-drawer.png`        |

## Phase-0 sign-off

Phase 0 does not require the PNG files to exist on disk — it requires the
catalog above to be correct and complete against the frozen HTML. Later
sprints (Phase 6 Visual QA) populate this folder with actual golden images.
