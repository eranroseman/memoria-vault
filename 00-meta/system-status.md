# System status

Runtime health snapshot. Refresh occasionally — typically when something feels off or after a major config change. **Distinct from [[01-dashboards/index|the Daily Health dashboard]]**, which tracks work in flight; this file tracks whether the system *itself* is up.

## Components

| Component | Status | Last verified |
| --- | --- | --- |
| Hermes installed | *(unknown)* | — |
| Policy MCP running | *(unknown)* | — |
| Tasks MCP running | *(unknown)* | — |
| ACP connection | *(unknown)* | — |
| Cron scheduler | *(unknown)* | — |
| Zotero local API | *(unknown)* | — |

## Profile availability

| Profile | Installed | Last invoked |
| --- | --- | --- |
| `memoria-librarian` | *(unknown)* | — |
| `memoria-mapper` | *(unknown)* | — |
| `memoria-socratic` | *(unknown)* | — |
| `memoria-writer` | *(unknown)* | — |
| `memoria-verifier` | *(unknown)* | — |
| `memoria-coder` | *(unknown)* | — |
| `memoria-linter` | *(unknown)* | — |

## Last verified

- **Date:** *(refresh)*
- **By:** *(human name)*
- **Command:** `hermes status` (or equivalent)

## Recent issues

- *(none, or describe)*

---

**When to update this file.** After running the install script. After a config change. When something breaks. Otherwise leave it alone — the [[01-dashboards/index|Daily Health dashboard]] surfaces live signals; this file is the static snapshot. See [[04-reference/safe-mode|safe-mode]] for procedures when components are down.
