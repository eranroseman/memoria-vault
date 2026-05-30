---
topic: plugins
---

# pdf-plus (PDF++)

> **Verify setting keys against your installed version.** The key names below describe the *intended behavior*; they have not been validated against an installed PDF++ build and the plugin's real keys differ (e.g. the color palette is indexed). Confirm the exact keys in the plugin's settings / `data.json` before relying on them.

Load-bearing settings:

- `enableHoverHighlight: true` — required for cite-on-hover behavior.
- `copyLinkFormat` — choose the format that includes the citekey and page (`[[{{citekey}}#p={{page}}]]` or similar). Without page-level granularity, the deep-linking value is lost.
- `defaultColorPalette` — keep stable across the vault. Color-coded highlights become semantically meaningful (e.g., red = contradicts, green = supports) only if the palette doesn't shift.
