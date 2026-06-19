# Skill state

Which skills are active in which lane — read live from the runtime layer (`.memoria/lane-overrides/*.yaml` + `.memoria/profiles/*/skills/`), which is the system of record for skill governance (ADR-43: dashboard-only). Open after adding or moving a skill, after editing a lane override, or when a lane behaves as if a skill is missing. Permissions: [Profile policies](https://eranroseman.github.io/memoria-vault/reference/profiles) · design: [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/operational-health/skill-state).

The **consistency checks** table is the decision queue — a row means the lane policy and the shipped skills disagree; fix the override or the skill folder. Empty is success. The two tables above it are the inventory the checks are computed from.

```dataviewjs
const adapter = app.vault.adapter;
const LANES = ".memoria/lane-overrides";
const PROFILES = ".memoria/profiles";

// --- minimal readers for the two controlled formats (no YAML lib in Dataview).
// The shapes these assume are pinned by tests/test_skill_state_dashboard.py.

// lane-override: policy.allow.skills / policy.deny.skills as flat "- name" lists.
function laneSkills(text) {
  const out = { allow: [], deny: [] };
  let section = null, inSkills = false;
  for (const raw of text.split("\n")) {
    const line = raw.replace(/(^|\s)#.*$/, "");
    if (!line.trim()) continue;
    const indent = line.match(/^ */)[0].length;
    const t = line.trim();
    if (indent === 2 && (t === "allow:" || t === "deny:")) {
      section = t.slice(0, -1); inSkills = false; continue;
    }
    if (indent <= 2) { section = null; inSkills = false; }
    if (section && indent === 4) inSkills = (t === "skills:");
    else if (section && inSkills && t.startsWith("- ")) out[section].push(t.slice(2).trim());
  }
  return out;
}

// SKILL.md frontmatter: name + metadata.memoria.{skill_id, profile, lane} + related_skills.
function skillMeta(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---/);
  const fm = m ? m[1] : "";
  const grab = (re) => { const g = fm.match(re); return g ? g[1].trim() : null; };
  const rel = fm.match(/related_skills:\s*\[([^\]]*)\]/);
  return {
    name: grab(/^name:\s*(.+)$/m),
    skill_id: grab(/skill_id:\s*"?([^"\n]+?)"?\s*$/m),
    profile: grab(/^\s+profile:\s*(\S+)/m),
    lane: grab(/^\s+lane:\s*(\S+)/m),
    related: rel ? rel[1].split(",").map(s => s.trim()).filter(Boolean) : [],
  };
}

const base = (p) => p.split("/").pop();

let laneFiles, profileDirs;
try {
  laneFiles = (await adapter.list(LANES)).files.filter(f => f.endsWith(".yaml"));
  profileDirs = (await adapter.list(PROFILES)).folders.filter(f => base(f).startsWith("memoria-"));
} catch (e) {
  dv.paragraph("_`.memoria/` is not readable from this vault — this dashboard reads the runtime layer shipped inside the vault (`.memoria/lane-overrides/`, `.memoria/profiles/*/skills/`). If those folders exist on disk, the vault adapter could not list them; check that the vault root is the folder that contains `.memoria/`._");
  return;
}

// lane policies, keyed by profile name (copi.yaml -> memoria-copi)
const lanes = {};
for (const f of laneFiles) {
  lanes["memoria-" + base(f).replace(/\.yaml$/, "")] = laneSkills(await adapter.read(f));
}

// shipped skills per profile
const shipped = {};   // profile -> [{folder, meta|null}]
for (const dir of profileDirs) {
  const profile = base(dir);
  shipped[profile] = [];
  let folders = [];
  try { folders = (await adapter.list(dir + "/skills")).folders; } catch (e) { /* no skills/ */ }
  for (const sf of folders) {
    let meta = null;
    try { meta = skillMeta(await adapter.read(sf + "/SKILL.md")); } catch (e) { /* missing SKILL.md */ }
    shipped[profile].push({ folder: base(sf), meta });
  }
}

const profiles = [...new Set([...Object.keys(lanes), ...Object.keys(shipped)])].sort();
const total = Object.values(shipped).reduce((n, l) => n + l.length, 0);

dv.header(2, "Lane policy at a glance");
dv.paragraph(`${total} shipped skills across ${Object.keys(shipped).length} profiles. \`allow\`/\`deny\` are the lane ceiling's runtime skill gates; *shipped* counts the \`SKILL.md\` folders the profile actually carries.`);
dv.table(
  ["Profile", "Allowed runtime skills", "Denied runtime skills", "Shipped"],
  profiles.map(p => [
    p,
    (lanes[p]?.allow ?? []).join(", ") || "—",
    (lanes[p]?.deny ?? []).join(", ") || "—",
    (shipped[p] ?? []).length,
  ])
);

dv.header(2, "Shipped skills");
const rows = [];
for (const p of profiles) {
  for (const s of shipped[p] ?? []) {
    rows.push([p, s.folder, s.meta?.lane ?? "?", s.meta?.skill_id ?? "?", (s.meta?.related ?? []).join(", ") || "—"]);
  }
}
dv.table(["Profile", "Skill", "Lane", "Skill id", "Relies on"], rows);

dv.header(2, "Consistency checks");
dv.paragraph("A row is a disagreement between the lane policy and the shipped skills — empty is success. \"Outside allow list\" rows need a verdict: either the dependency is an MCP server (fine — MCP access is governed by `config.yaml`, not the skill gate) or the skill metadata / lane override is stale.");
const checks = [];
for (const p of profiles) {
  if (!(p in lanes)) checks.push([p, "—", "no lane-override file for this profile"]);
  if (!(p in shipped)) checks.push([p, "—", "lane-override exists but no profile folder ships"]);
}
const seenIds = {};
for (const p of profiles) {
  for (const s of shipped[p] ?? []) {
    if (!s.meta) { checks.push([p, s.folder, "SKILL.md missing or unreadable"]); continue; }
    if (s.meta.name !== s.folder) checks.push([p, s.folder, `frontmatter name '${s.meta.name}' ≠ folder name`]);
    if (s.meta.profile && s.meta.profile !== p) checks.push([p, s.folder, `frontmatter profile '${s.meta.profile}' ≠ shipping profile`]);
    if (s.meta.skill_id) {
      if (s.meta.skill_id in seenIds) checks.push([p, s.folder, `duplicate skill_id '${s.meta.skill_id}' (also ${seenIds[s.meta.skill_id]})`]);
      seenIds[s.meta.skill_id] = `${p}/${s.folder}`;
    }
    const allow = lanes[p]?.allow ?? [], deny = lanes[p]?.deny ?? [];
    for (const r of s.meta.related) {
      if (deny.includes(r)) checks.push([p, s.folder, `relies on '${r}', which the lane denies`]);
      else if (allow.length && !allow.includes(r)) checks.push([p, s.folder, `relies on '${r}', outside the lane's allow list`]);
    }
  }
}
if (checks.length) dv.table(["Profile", "Skill", "Finding"], checks);
else dv.paragraph("_No mismatches — lane policy and shipped skills agree._");
```

## What this dashboard is not

**Not a lifecycle tracker.** ADR-43's full shape — an intake→archived state machine with per-skill governance notes in `system/skills/` — was considered and not adopted (single-researcher scope); there is no skill state beyond *shipped and allowed*. Adding a skill stays a runtime operation: drop the `SKILL.md` into the profile's `skills/` folder and, if it needs a new runtime gate, edit the lane override.

**Not an enforcement surface.** The policy gate enforces; this view only renders what the runtime layer says (the Linter is the integrity monitor; dashboards are the view layer).
