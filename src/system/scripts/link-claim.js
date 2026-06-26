/*
 * QuickAdd user script — "Memoria: link claim".
 *
 * Direct palette access to the link lane (#203): defaults to the active note
 * when it is a claim (under notes/claims/), otherwise prompts for the claim
 * note path. It writes the deterministic [!suggestions] top-K callout in-place,
 * then creates a correctly-addressed card on the Librarian
 * (`hermes kanban create --skill link-suggest-claim`). Mirrors
 * delegate-task.js: the card-create goes through `bash -lc` so it reaches the
 * native Hermes CLI.
 */

const LANE = "link";
const ASSIGNEE = "memoria-librarian";
const SKILL = "link-suggest-claim";
const CLAIM_PREFIX = "notes/claims/";
const SUGGESTION_LIMIT = 10;
const { appendCallout, fnv1a, queueHermesCard } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));
const STOPWORDS = new Set([
  "about", "after", "again", "against", "also", "because", "before", "between",
  "claim", "could", "from", "have", "into", "more", "note", "only", "paper",
  "should", "source", "their", "there", "these", "this", "through", "under",
  "where", "which", "while", "with", "would",
]);

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");

  const active = params.app.workspace.getActiveFile();
  let ref = active && active.path.startsWith(CLAIM_PREFIX) ? active.path : "";
  if (!ref) {
    ref = (await params.quickAddApi.inputPrompt("Claim note path to suggest links for:"))?.trim();
  }
  if (!ref) {
    new Notice("No claim note given.", 4000);
    return;
  }

  const claim = params.app.vault.getAbstractFileByPath(ref);
  if (!claim) {
    new Notice("Claim note not found: " + ref, 6000);
    return;
  }

  const claimText = await params.app.vault.read(claim);
  const suggestions = await rankLinkSuggestions(params.app, claim, claimText);
  await appendCallout(params.app, claim, buildSuggestionsCallout(suggestions));

  const body =
    "delegate:" + LANE + " — from the palette. Suggest links for the claim " + ref + ". " +
    "The deterministic [!suggestions] top-K callout has been written to the claim note. " +
    "Use the " + SKILL + " skill, add any optional LLM one-line explanations, propose forward " +
    "and backward link candidates through the normal proposal path, then kanban_complete with " +
    "review_status: requested.";
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(ref);

  new Notice("Wrote [!suggestions]; delegating to the " + LANE + " lane…", 3000);
  try {
    await queueHermesCard(cp, {
      title: "Link claim: " + ref,
      assignee: ASSIGNEE,
      skill: SKILL,
      idemKey,
      body,
      lane: LANE,
    });
    new Notice("✓ Suggestions written; link task queued. Watch Inbox > Activity. Needs me changes only if action is needed.", 15000);
  } catch (e) {
    new Notice(("Link delegation failed after writing suggestions: " + e.message).slice(0, 250), 10000);
  }
};

async function rankLinkSuggestions(app, claim, claimText) {
  const targetTerms = termSet(claimText);
  const files = app.vault.getMarkdownFiles()
    .filter((f) => f.path !== claim.path)
    .filter((f) => f.path.startsWith("notes/claims/") || f.path.startsWith("notes/sources/"));
  const scored = [];
  for (const file of files) {
    const text = await app.vault.cachedRead(file);
    if (file.path.startsWith("notes/claims/") && isSupersededClaim(text)) continue;
    const terms = termSet(text);
    const shared = [...targetTerms].filter((term) => terms.has(term));
    if (!shared.length) continue;
    const denom = Math.max(targetTerms.size, terms.size, 1);
    scored.push({ file, score: shared.length / denom, shared: shared.slice(0, 5) });
  }
  return scored
    .sort((a, b) => b.score - a.score || a.file.path.localeCompare(b.file.path))
    .slice(0, SUGGESTION_LIMIT);
}

function isSupersededClaim(text) {
  const fm = String(text).match(/^---\n([\s\S]*?)\n---/);
  if (!fm) return false;
  const line = fm[1].split(/\r?\n/).find((l) => /^superseded_by:\s*/.test(l));
  if (!line) return false;
  const value = line.replace(/^superseded_by:\s*/, "").trim();
  return Boolean(value && value !== '""' && value !== "''" && value.toLowerCase() !== "null");
}

function buildSuggestionsCallout(candidates) {
  const today = new Date().toISOString().slice(0, 10);
  const lines = [
    "> [!suggestions]- Link suggestions (updated " + today + ")",
    "> Deterministic top-K from local claim/source overlap. Optional Librarian one-line explanations are queued on the link card.",
  ];
  if (!candidates.length) {
    lines.push("> - No local candidates crossed the deterministic overlap floor.");
    return lines.join("\n");
  }
  const forward = candidates.slice(0, 5);
  const backward = candidates.slice(5, 10);
  lines.push("> **Forward candidates**");
  for (const item of forward) lines.push("> - [ ] " + candidateLine(item));
  if (backward.length) {
    lines.push("> **Backward candidates**");
    for (const item of backward) lines.push("> - [ ] " + candidateLine(item));
  }
  return lines.join("\n");
}

function candidateLine(item) {
  const stem = item.file.path.replace(/\.md$/, "");
  const label = item.file.basename;
  const terms = item.shared.length ? " · shared: " + item.shared.join(", ") : "";
  return "[[" + stem + "|" + label + "]] — score " + item.score.toFixed(3) + terms;
}

function termSet(text) {
  const terms = String(text).toLowerCase().match(/[a-z][a-z0-9-]{3,}/g) || [];
  return new Set(terms.filter((term) => !STOPWORDS.has(term)));
}
