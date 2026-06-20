/*
 * QuickAdd user script — "Memoria: verify draft".
 *
 * Direct palette access to the verify lane (#203): defaults to the active
 * note when it is a draft (under projects/), otherwise prompts for the draft
 * path. It writes a deterministic [!verification] preflight callout in-place,
 * then creates a correctly-addressed card on the Peer-reviewer
 * (`hermes kanban create --skill verify-check-citation`). Mirrors
 * delegate-task.js: the card-create goes through `bash -lc` so it reaches the
 * native Hermes CLI.
 */

const LANE = "verify";
const ASSIGNEE = "memoria-peer-reviewer";
const SKILL = "verify-check-citation";
const DRAFT_PREFIX = "projects/";
const { appendCallout, fnv1a, run, shq, uniquePath, yamlString } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");

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
  const ungrounded = detectUngroundedAssertions(draftText);
  await appendCallout(params.app, draft, buildVerificationCallout(trace));
  const gapCards = await writeKnowledgeGapCards(params.app, ref, ungrounded);

  const body =
    "delegate:" + LANE + " — from the palette. Verify the draft " + ref + ". " +
    "The deterministic [!verification] preflight callout has been written to the draft. " +
    gapCards.length + " visible knowledge-gap card(s) were staged for ungrounded assertions. " +
    "Use the " + SKILL + " skill: trace every substantive claim back to its claim note or " +
    "citekey, report traced and untraced claims, then kanban_complete with " +
    "review_status: requested.";
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(ref);

  new Notice("Wrote [!verification]; delegating to the " + LANE + " lane…", 3000);
  try {
    await run(cp,
      "hermes kanban create " + shq("Verify draft: " + ref) +
      " --assignee " + ASSIGNEE + " --skill " + SKILL + " --created-by quickadd" +
      " --idempotency-key " + shq(idemKey) +
      " --body " + shq(body)
    );
    new Notice("✓ Verification callout written; " + gapCards.length + " gap card(s) staged; card created on the " + LANE + " lane (" + ASSIGNEE + ").", 7000);
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

function detectUngroundedAssertions(text) {
  const lines = String(text).split(/\n+/);
  const assertions = [];
  for (const raw of lines) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || line.startsWith(">") || line.startsWith("```")) continue;
    if (line.includes("[[") || /@[A-Za-z][A-Za-z0-9_:-]+/.test(line)) continue;
    const sentenceLike = /[.!?]$/.test(line) && line.split(/\s+/).length >= 8;
    if (sentenceLike) assertions.push(line.replace(/^[-*]\s+/, ""));
  }
  return unique(assertions).slice(0, 12);
}

async function writeKnowledgeGapCards(app, draftPath, assertions) {
  const cards = [];
  for (const assertion of assertions) {
    const path = await uniquePath(app.vault.adapter, "inbox/gap-draft-" + fnv1a(draftPath + assertion) + ".md");
    const today = new Date().toISOString().slice(0, 10);
    const text = [
      "---",
      "title: " + yamlString("Ground draft assertion"),
      "type: gap",
      "lifecycle: proposed",
      "gap_type: additive",
      "action: " + yamlString("Link or create support for an ungrounded assertion in " + draftPath),
      "argument_for: " + yamlString(assertion),
      "argument_against: " + yamlString("The assertion has no claim link or citekey in the deterministic preflight."),
      "what_tipped_it: " + yamlString("Writer draft verification found a sentence-like assertion without grounding markers."),
      "certainty: likely",
      "raised_by: quickadd-verify-draft",
      "loudness: notice",
      "target: " + yamlString(draftPath),
      "created: " + today,
      "---",
      "",
      "# Assertion",
      "",
      assertion,
      "",
    ].join("\n");
    await app.vault.adapter.write(path, text);
    cards.push(path);
  }
  return cards;
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

function unique(values) {
  return [...new Set(values.filter(Boolean))].sort();
}
