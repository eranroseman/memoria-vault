/*
 * QuickAdd user script — "Memoria: verify draft".
 *
 * Direct palette access to the verify lane (#203): defaults to the active
 * note when it is a draft (under projects/), otherwise prompts for the draft
 * path. It writes a deterministic [!verification] preflight callout in-place,
 * then creates a correctly-addressed card on the Peer-reviewer
 * (`hermes kanban create --skill verify-check-citation`). Mirrors
 * delegate-task.js: the card-create goes through `bash -lc` (wrapped in
 * wsl.exe on Windows) so it reaches hermes in WSL.
 */

const LANE = "verify";
const ASSIGNEE = "memoria-peer-reviewer";
const SKILL = "verify-check-citation";
const DRAFT_PREFIX = "projects/";

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");
  const onWindows = process.platform === "win32";

  const run = (sh) =>
    new Promise((resolve, reject) => {
      const file = onWindows ? "wsl.exe" : "bash";
      const args = onWindows ? ["bash", "-lc", sh] : ["-lc", sh];
      cp.execFile(file, args, { timeout: 30000, maxBuffer: 1 << 20 }, (err, stdout, stderr) => {
        if (err) return reject(new Error(String(stderr || err.message || "").trim()));
        resolve(stdout);
      });
    });

  const active = params.app.workspace.getActiveFile();
  let ref = active && active.path.startsWith(DRAFT_PREFIX) ? active.path : "";
  if (!ref) {
    ref = (await params.quickAddApi.inputPrompt("Draft path to verify:"))?.trim();
  }
  if (!ref) {
    new Notice("No draft given.", 4000);
    return;
  }

  const draft = params.app.vault.getAbstractFileByPath(ref);
  if (!draft) {
    new Notice("Draft not found: " + ref, 6000);
    return;
  }

  const draftText = await params.app.vault.read(draft);
  const trace = traceDraftMarkers(draftText);
  await appendCallout(params.app, draft, buildVerificationCallout(trace));

  const body =
    "delegate:" + LANE + " — from the palette. Verify the draft " + ref + ". " +
    "The deterministic [!verification] preflight callout has been written to the draft. " +
    "Use the " + SKILL + " skill: trace every substantive claim back to its claim note or " +
    "citekey, report traced and untraced claims, then kanban_complete with " +
    "review_status: requested.";
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(ref);

  new Notice("Wrote [!verification]; delegating to the " + LANE + " lane…", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Verify draft: " + ref) +
      " --assignee " + ASSIGNEE + " --skill " + SKILL + " --created-by quickadd" +
      " --idempotency-key " + shq(idemKey) +
      " --body " + shq(body)
    );
    new Notice("✓ Verification callout written; card created on the " + LANE + " lane (" + ASSIGNEE + ").", 6000);
  } catch (e) {
    new Notice(("Verify delegation failed after writing callout: " + e.message).slice(0, 250), 10000);
  }
};

function traceDraftMarkers(text) {
  const claimLinks = unique([...String(text).matchAll(/\[\[([^\]|#]*(?:notes\/claims\/)?[^\]|#]*)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]/g)]
    .map((m) => m[1])
    .filter((link) => link.includes("notes/claims/") || !link.includes("/")));
  const citekeys = unique([...String(text).matchAll(/@([A-Za-z][A-Za-z0-9_:-]+)/g)].map((m) => m[1]));
  return { claimLinks, citekeys };
}

function buildVerificationCallout(trace) {
  const today = new Date().toISOString().slice(0, 10);
  const lines = [
    "> [!verification] Verification trace (updated " + today + ")",
    "> Deterministic preflight before the Peer-reviewer lane; the card performs the support judgment.",
    "> - Claim links found: " + trace.claimLinks.length,
    "> - Citekeys found: " + trace.citekeys.length,
  ];
  for (const link of trace.claimLinks.slice(0, 10)) lines.push(">   - ✓ [[" + link + "]]");
  for (const citekey of trace.citekeys.slice(0, 10)) lines.push(">   - @" + citekey);
  if (!trace.claimLinks.length && !trace.citekeys.length) {
    lines.push("> - ⚑ No claim links or citekeys found in this draft preflight.");
  }
  return lines.join("\n");
}

async function appendCallout(app, file, callout) {
  const text = await app.vault.read(file);
  await app.vault.modify(file, text.trimEnd() + "\n\n" + callout + "\n");
}

function unique(values) {
  return [...new Set(values.filter(Boolean))].sort();
}

function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}

function fnv1a(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h * 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}
