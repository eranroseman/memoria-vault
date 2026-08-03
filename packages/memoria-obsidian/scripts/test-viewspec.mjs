import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const {
  KNOWN_BLOCK_KINDS,
  VIEW_SPEC_VERSION,
  collapseAnalysis,
  materialize,
  moveSelection,
  renderBlock,
  renderView,
  sortCards,
} = require("../../../src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/viewspec.js");

function texts(tree) {
  return [tree.text, ...(tree.children || []).flatMap(texts)].filter(Boolean);
}

test("catalog is closed at exactly five kinds", () => {
  assert.deepEqual(KNOWN_BLOCK_KINDS, ["card", "text", "badge", "action-row", "evidence-list"]);
  assert.equal(VIEW_SPEC_VERSION, "view-spec.v1");
  // The roster above is only a claim until every kind on it actually reaches a
  // renderer: narrowing the constant fails the deepEqual, and dropping a case
  // from renderBlock fails this loop.
  for (const kind of KNOWN_BLOCK_KINDS) {
    assert.notEqual(renderBlock({ kind, id: `probe-${kind}` }).cls, "memoria-block-unknown", kind);
  }
});

test("unknown block kind renders a labeled fallback box, never silence", () => {
  const tree = renderBlock({ kind: "table", id: "t1" });
  assert.equal(tree.cls, "memoria-block-unknown");
  assert.equal(tree.text, "Unknown block type: table");
  assert.equal(tree.children[0].tag, "pre");
  assert.ok(tree.children[0].text.includes('"table"'));
});

// Producer state: transport hands the pane whatever JSON arrived, so a
// malformed or future payload can put a non-object where a block belongs. It
// must fail visible with its raw content, not throw and blank the pane.
test("a non-object block still fails visible", () => {
  const nulled = renderBlock(null);
  assert.equal(nulled.cls, "memoria-block-unknown");
  assert.equal(nulled.text, "Unknown block type: null");
  const scalar = renderBlock("card");
  assert.equal(scalar.cls, "memoria-block-unknown");
  assert.equal(scalar.children[0].text, '"card"');
});

test("unknown view version renders a labeled fallback", () => {
  const trees = renderView({ version: "view-spec.v2", blocks: [] });
  assert.equal(trees.length, 1);
  assert.equal(trees[0].cls, "memoria-block-unknown");
  assert.equal(trees[0].text, "Unknown view-spec version: view-spec.v2");
});

// Producer state: the summary poll response carries no `view` key at all
// (contract: `summary=true` has no view), so a mis-wired caller hands
// renderView `undefined` rather than a versioned envelope.
test("an absent view renders the same labeled fallback", () => {
  const trees = renderView(undefined);
  assert.equal(trees.length, 1);
  assert.equal(trees[0].cls, "memoria-block-unknown");
  assert.equal(trees[0].text, "Unknown view-spec version: undefined");
});

// Producer state: a view envelope serialized without its (empty) block list.
test("a known-version view with no block list renders nothing, and does not throw", () => {
  assert.deepEqual(renderView({ version: VIEW_SPEC_VERSION }), []);
});

test("renderView renders every block of a known version in payload order", () => {
  const trees = renderView({
    version: "view-spec.v1",
    blocks: [
      { kind: "text", id: "t1", text: "first" },
      { kind: "badge", id: "b1", label: "second" },
    ],
  });
  assert.deepEqual(
    trees.map((tree) => [tree.cls, tree.text]),
    [
      ["memoria-block-text", "first"],
      ["memoria-badge", "second"],
    ],
  );
});

// Producer state: the engine's forward-compat contract (U3-ENG.5) — a later
// engine adds a block kind, and the HTTP transport carries it through
// unfiltered (tests/test_attention_view.py::
// test_http_dispatch_passes_additive_unknown_blocks_through). This is the
// pane's half of that claim: the new block must join the view visibly, between
// the known cards that keep their places, rather than vanish or displace them.
test("an additive future block joins the view without displacing known ones", () => {
  const trees = renderView({
    version: "view-spec.v1",
    blocks: [
      { kind: "card", id: "c1", title: "First", kind_line: "flag", blocks: [] },
      { kind: "sparkline", id: "future", points: [1, 2, 3] },
      { kind: "card", id: "c2", title: "Second", kind_line: "flag", blocks: [] },
    ],
  });
  assert.deepEqual(
    trees.map((tree) => tree.cls),
    ["memoria-card", "memoria-block-unknown", "memoria-card"],
  );
  assert.deepEqual(
    [trees[0], trees[2]].map((tree) => tree.children[1].text),
    ["First", "Second"],
  );
  assert.equal(trees[1].text, "Unknown block type: sparkline");
  assert.ok(trees[1].children[0].text.includes('"points"'));
});

// ... and one nested inside a card, which is where the first additive kind
// actually lands: renderCard maps every declared child through renderBlock, so
// an unknown child must fail visible in place instead of blanking the card.
test("an additive future child block fails visible inside its card", () => {
  const tree = renderBlock({
    kind: "card",
    id: "c1",
    title: "Card",
    kind_line: "flag",
    blocks: [
      { kind: "text", id: "t1", text: "known" },
      { kind: "timeline", id: "future-child", at: "2026-08-01" },
    ],
  });
  assert.deepEqual(
    tree.children.map((child) => child.cls),
    ["memoria-card-kind", "memoria-card-title", "memoria-block-text", "memoria-block-unknown"],
  );
  assert.equal(tree.children[3].text, "Unknown block type: timeline");
});

test("card preserves declared semantic child order and appends present analysis", () => {
  const tree = renderBlock({
    kind: "card",
    id: "ev1",
    ref: "projects/alpha/draft.md#^blk-1234",
    title: "Claim",
    kind_line: "evidence-review",
    argument_for: "ground",
    argument_against: "counter-ground",
    tipped_by: "implicit derivation",
    certainty: "possible",
    raised_by: "review-sweep",
    raised_at: "2026-07-29T12:00:00Z",
    blocks: [
      { kind: "evidence-list", id: "e1", items: [{ label: "Source", ref: "notes/source.md" }] },
      { kind: "text", id: "r1", text: "Routing: implicit" },
      {
        kind: "action-row",
        id: "a1",
        actions: [
          {
            label: "Resolve",
            operation_id: "resolve-attention",
            payload: { target_id: "inbox/claim.md" },
            primary: true,
          },
          {
            label: "Defer",
            operation_id: "resolve-attention",
            payload: { target_id: "inbox/claim.md", outcome: "defer" },
          },
        ],
      },
    ],
  });
  const classes = tree.children.map((child) => child.cls);
  assert.deepEqual(classes, [
    "memoria-card-kind",
    "memoria-card-title",
    "memoria-evidence",
    "memoria-block-text",
    "memoria-action-row",
    "memoria-card-arguments",
    "memoria-card-tipped",
    "memoria-card-meta",
  ]);
  assert.equal(tree.attrs["data-ref"], "projects/alpha/draft.md#^blk-1234");
  assert.equal(tree.children[2].children[0].attrs["data-ref"], "notes/source.md");
  const [resolve, defer] = tree.children[4].children;
  assert.equal(resolve.text, "Resolve");
  assert.equal(resolve.cls, "memoria-action memoria-action-primary");
  assert.equal(resolve.attrs["data-operation-id"], "resolve-attention");
  assert.deepEqual(JSON.parse(resolve.attrs["data-payload"]), { target_id: "inbox/claim.md" });
  assert.equal(defer.text, "Defer");
  assert.equal(defer.cls, "memoria-action");
  assert.equal(defer.attrs["data-operation-id"], "resolve-attention");
  assert.deepEqual(JSON.parse(defer.attrs["data-payload"]), {
    target_id: "inbox/claim.md",
    outcome: "defer",
  });
  assert.deepEqual(
    tree.children[5].children.map((child) => child.cls),
    ["memoria-card-for", "memoria-card-against"],
  );
  assert.deepEqual(texts(tree.children[5]), ["ground", "counter-ground"]);
  assert.deepEqual(
    tree.children[6].children.map((child) => child.text),
    ["tipped by: implicit derivation", "possible"],
  );
  assert.equal(tree.children[7].text, "raised by review-sweep · 2026-07-29T12:00:00Z");
});

test("cure card does not create absent analysis or action trees", () => {
  const tree = renderBlock({
    kind: "card",
    id: "ev2",
    ref: "projects/alpha/draft.md#^blk-5678",
    title: "Repair grounding",
    kind_line: "evidence-text-drift",
    blocks: [
      { kind: "evidence-list", id: "e2", items: [] },
      { kind: "text", id: "r2", text: "Repair the marker." },
    ],
  });
  const classes = tree.children.map((child) => child.cls);
  assert.deepEqual(classes, [
    "memoria-card-kind",
    "memoria-card-title",
    "memoria-evidence",
    "memoria-block-text",
  ]);
});

test("card maps repeated semantic children once in their supplied order", () => {
  const tree = renderBlock({
    kind: "card",
    id: "repeat",
    title: "Repeat",
    kind_line: "test",
    blocks: [
      { kind: "text", id: "first", text: "First" },
      { kind: "text", id: "second", text: "Second" },
    ],
  });
  assert.deepEqual(
    tree.children.map((child) => child.cls),
    ["memoria-card-kind", "memoria-card-title", "memoria-block-text", "memoria-block-text"],
  );
  assert.deepEqual(
    tree.children.slice(2).map((child) => child.text),
    ["First", "Second"],
  );
});

test("one-sided analysis renders only its present field", () => {
  const tree = renderBlock({
    kind: "card",
    id: "one-sided",
    title: "One",
    kind_line: "test",
    argument_for: "supported",
    certainty: "likely",
    blocks: [],
  });
  assert.deepEqual(
    tree.children[2].children.map((child) => child.cls),
    ["memoria-card-for"],
  );
  assert.deepEqual(
    tree.children[3].children.map((child) => child.cls),
    ["memoria-certainty-chip"],
  );
});

test("one-sided metadata has no empty provenance slot or separator", () => {
  const raisedBy = renderBlock({
    kind: "card",
    id: "raised-by",
    title: "By",
    kind_line: "test",
    raised_by: "review-sweep",
    blocks: [],
  });
  const raisedAt = renderBlock({
    kind: "card",
    id: "raised-at",
    title: "At",
    kind_line: "test",
    raised_at: "2026-07-29T12:00:00Z",
    blocks: [],
  });
  assert.equal(raisedBy.children[2].cls, "memoria-card-meta");
  assert.equal(raisedBy.children[2].text, "raised by review-sweep");
  assert.equal(raisedAt.children[2].cls, "memoria-card-meta");
  assert.equal(raisedAt.children[2].text, "2026-07-29T12:00:00Z");
});

test("loudness is rendered verbatim and missing loudness gets no loudness class", () => {
  const odd = renderBlock({ kind: "badge", id: "b1", label: "x", loudness: "shout" });
  assert.equal(odd.cls, "memoria-badge memoria-loudness-shout");
  const none = renderBlock({ kind: "badge", id: "b2", label: "x" });
  assert.equal(none.cls, "memoria-badge");
});

// Producer state: every attention card carries a loudness band, and the pane
// colours the card and its kind line from it. Rendering it on the badge alone
// would leave the queue rows unbanded.
test("a card carries its payload loudness on the card and its kind line", () => {
  const tree = renderBlock({
    kind: "card",
    id: "loud",
    title: "Loud",
    kind_line: "unchecked-note",
    loudness: "alert",
    blocks: [],
  });
  assert.equal(tree.cls, "memoria-card memoria-loudness-alert");
  assert.equal(tree.children[0].cls, "memoria-card-kind memoria-loudness-alert");
  const unbanded = renderBlock({
    kind: "card",
    id: "quiet",
    title: "Q",
    kind_line: "k",
    blocks: [],
  });
  assert.equal(unbanded.cls, "memoria-card");
  assert.equal(unbanded.children[0].cls, "memoria-card-kind");
});

// Producer state: the engine emits `items: []` for an attention card with no
// target, and a labelless row is what any producer that knows only a ref emits.
test("evidence rows survive an empty list and a labelless item", () => {
  const empty = renderBlock({ kind: "evidence-list", id: "e0", items: [] });
  assert.equal(empty.cls, "memoria-evidence");
  assert.deepEqual(empty.children, []);
  const rows = renderBlock({
    kind: "evidence-list",
    id: "e1",
    items: [{ label: "Smith 2024", ref: "sources/smith-2024.md" }, { ref: "notes/bare.md" }],
  });
  assert.deepEqual(
    rows.children.map((child) => [child.text, child.attrs["data-ref"]]),
    [
      ["Smith 2024", "sources/smith-2024.md"],
      ["notes/bare.md", "notes/bare.md"],
    ],
  );
});

// Producer state: any field a payload omits. The module renders payloads
// verbatim, so an absent field must degrade to empty — printing the literal
// word `undefined` invents content, and a `data-payload` of "undefined" throws
// when the pane's click handler parses it.
test("an omitted payload field renders empty, never the word undefined", () => {
  assert.equal(renderBlock({ kind: "text", id: "t" }).text, "");
  assert.equal(renderBlock({ kind: "badge", id: "b" }).text, "");
  const row = renderBlock({
    kind: "action-row",
    id: "a",
    actions: [{ operation_id: "resolve-attention" }],
  });
  assert.equal(row.children[0].text, "");
  assert.deepEqual(JSON.parse(row.children[0].attrs["data-payload"]), {});
});

// Producer state: every kind the catalog dispatches. The pane walks
// `tree.children` and reads `tree.attrs[...]`, so both slots must exist on
// every tree the renderer can return, not only on the kinds that fill them.
test("every rendered tree carries the declared attrs and children slots", () => {
  for (const kind of [...KNOWN_BLOCK_KINDS, "table"]) {
    const tree = renderBlock({ kind, id: `slots-${kind}` });
    assert.ok(Array.isArray(tree.children), kind);
    assert.equal(typeof tree.attrs, "object", kind);
    assert.notEqual(tree.attrs, null, kind);
  }
});

// Producer state: transport hands the pane whatever JSON arrived, so `blocks`
// can be a non-array. The card must still render rather than blank the pane.
test("a card whose blocks field is not a list still renders", () => {
  const tree = renderBlock({
    kind: "card",
    id: "c1",
    title: "Title",
    kind_line: "unchecked-note",
    blocks: "oops",
  });
  assert.deepEqual(
    tree.children.map((child) => child.cls),
    ["memoria-card-kind", "memoria-card-title"],
  );
});

test("sortCards pins block, then loudness rank, then oldest first", () => {
  // Every band the engine can write appears: `lib/inbox.py:21` defines
  // ("quiet", "notice", "alert", "block") and validates it on write, and
  // `notice` is the default for a written proposal, so a rank typo between
  // `notice` and `alert` would misorder the commonest card in the queue.
  const cards = [
    { ref: "a", loudness: "quiet", age_s: 50 },
    { ref: "b", loudness: "block", age_s: 1 },
    { ref: "c", loudness: "alert", age_s: 10 },
    { ref: "d", loudness: "alert", age_s: 99 },
    { ref: "e", loudness: "weird", age_s: 5 },
    { ref: "n", loudness: "notice", age_s: 7 },
  ];
  assert.deepEqual(
    sortCards(cards).map((card) => card.ref),
    ["b", "d", "c", "n", "a", "e"],
  );
  // The pane re-sorts the cards it cached from the last poll, so sorting must
  // not reorder the caller's array.
  assert.deepEqual(
    cards.map((card) => card.ref),
    ["a", "b", "c", "d", "e", "n"],
  );
});

// Producer state: loudness is rendered verbatim from note frontmatter, so a
// hand-edited or future band arrives unrecognized. It ranks last even when it
// is the oldest card, rather than tying with the quietest known band.
test("an unrecognized loudness ranks after every known band", () => {
  const cards = [
    { ref: "unknown", loudness: "murmur", age_s: 900 },
    { ref: "quiet", loudness: "quiet", age_s: 1 },
  ];
  assert.deepEqual(
    sortCards(cards).map((card) => card.ref),
    ["quiet", "unknown"],
  );
});

// Producer state: a block that reaches the pane without `age_s` (an engine
// older than this contract, or another view's card). It must sort as the
// youngest card rather than scrambling the comparator with NaN.
test("a card missing age_s sorts last within its band, not at random", () => {
  const cards = [
    { ref: "old", loudness: "alert", age_s: 50 },
    { ref: "ageless", loudness: "alert" },
    { ref: "young", loudness: "alert", age_s: 10 },
  ];
  assert.deepEqual(
    sortCards(cards).map((card) => card.ref),
    ["old", "young", "ageless"],
  );
});

// Producer state: `created` is hand-editable frontmatter, so a date in the
// future makes `age_s` negative -- the one input on which this comparator and
// the engine's used to disagree (U3-PLUG.7 reconciliation, 2026-08-01). The
// fixture is the engine's own order from
// `test_attention_view_ages_cards_from_created`, plus a misbanded card at the
// front so an inert comparator cannot pass by leaving the array alone.
test("a future-dated card keeps the engine's row order, not a younger-than-new one", () => {
  const cards = [
    { ref: "quiet", loudness: "quiet", age_s: 0 },
    { ref: "aged", loudness: "alert", age_s: 259200 },
    { ref: "today", loudness: "alert", age_s: 0 },
    { ref: "future", loudness: "alert", age_s: -259200 },
    { ref: "undated", loudness: "alert", age_s: 0 },
  ];
  assert.deepEqual(
    sortCards(cards).map((card) => card.ref),
    ["aged", "today", "future", "undated", "quiet"],
  );
});

test("moveSelection clamps j/k", () => {
  assert.equal(moveSelection(3, 0, "j"), 1);
  assert.equal(moveSelection(3, 2, "j"), 2);
  assert.equal(moveSelection(3, 0, "k"), 0);
  assert.equal(moveSelection(0, 0, "j"), 0);
});

// Producer state: the pane's keydown handler forwards every key it sees, so
// most keystrokes must leave the selection where it is.
test("moveSelection ignores keys that are not j or k", () => {
  assert.equal(moveSelection(3, 2, "x"), 2);
  assert.equal(moveSelection(3, 1, "Enter"), 1);
});

function stubTree() {
  const made = [];
  function stubEl(tag, parent) {
    const el = {
      tag,
      parent,
      attrs: {},
      children: [],
      createEl(childTag, options = {}) {
        const child = stubEl(childTag, el);
        child.cls = options.cls || "";
        child.text = options.text || "";
        el.children.push(child);
        made.push(child);
        return child;
      },
      setAttribute(key, value) {
        el.attrs[key] = value;
      },
    };
    return el;
  }
  return { made, root: stubEl("div", null) };
}

test("materialize walks the tree through createEl", () => {
  const { made, root } = stubTree();
  materialize(renderBlock({ kind: "text", id: "t", text: "hello" }), root);
  assert.equal(made.length, 1);
  assert.equal(made[0].tag, "p");
  assert.equal(made[0].text, "hello");
});

// Producer state: every real card is a nested tree with attributes on inner
// nodes — a walker that only creates the root element, or that sets attributes
// on the wrong element, renders an empty pane.
test("materialize descends into children and sets their attributes", () => {
  const { made, root } = stubTree();
  const returned = materialize(
    renderBlock({
      kind: "evidence-list",
      id: "e1",
      items: [
        { label: "Source", ref: "notes/source.md" },
        { label: "Other", ref: "notes/other.md" },
      ],
    }),
    root,
  );
  assert.equal(made.length, 3);
  assert.equal(returned, made[0]);
  assert.equal(made[0].tag, "div");
  assert.equal(made[0].cls, "memoria-evidence");
  assert.deepEqual(made[0].attrs, {});
  assert.deepEqual(
    made.slice(1).map((el) => [el.tag, el.parent, el.text, el.attrs["data-ref"]]),
    [
      ["a", made[0], "Source", "notes/source.md"],
      ["a", made[0], "Other", "notes/other.md"],
    ],
  );
  assert.deepEqual(root.children, [made[0]]);
});

// V2 spec section 3, structural not stylistic: the PI reads the grounds, the
// routing reason, and the four actions before the machine's opinion. These
// pin the *order* the disclosure leaves behind, because a transform that
// merely hides analysis while floating it above the evidence would satisfy
// "collapsed by default" and still lead with the machine.
test("collapseAnalysis preserves ordered semantic children before disclosure", () => {
  const card = renderBlock({
    kind: "card",
    id: "ev-0011aabb",
    ref: "projects/project-alpha/draft.md#^blk-a1b2",
    title: "Implicit synthesis claim",
    kind_line: "evidence-review",
    review_kind: "evidence-set",
    certainty: "possible",
    argument_for: "Both grounds items support the claim text.",
    argument_against: "The set is implicit; no span was cited.",
    tipped_by: "implicit derivation",
    blocks: [
      { kind: "evidence-list", id: "ev-0011aabb-grounds", items: [{ ref: "notes/a.md" }] },
      { kind: "text", id: "ev-0011aabb-routing", text: "Routing: implicit" },
      {
        kind: "action-row",
        id: "ev-0011aabb-actions",
        actions: [
          { label: "Accept", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "accept" } },
          { label: "Reject", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "reject" } },
          { label: "Edit", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "edit" } },
          { label: "Defer", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "defer" } },
        ],
      },
    ],
  });

  const collapsed = collapseAnalysis(card, false);
  const classes = collapsed.children.map((child) => child.cls);
  assert.deepEqual(classes, [
    "memoria-card-kind",
    "memoria-card-title",
    "memoria-evidence",
    "memoria-block-text",
    "memoria-action-row",
    "memoria-analysis-toggle",
    "memoria-analysis is-collapsed",
  ]);
  const toggle = collapsed.children[classes.indexOf("memoria-analysis-toggle")];
  assert.equal(toggle.tag, "button");
  assert.equal(toggle.text, "Show analysis (machine)");
  assert.deepEqual(toggle.attrs, { "data-toggle-analysis": "1" });
  const container = collapsed.children[classes.indexOf("memoria-analysis is-collapsed")];
  assert.deepEqual(
    container.children.map((child) => child.cls),
    ["memoria-card-arguments", "memoria-card-tipped"],
    "both analysis groups move, in their rendered order",
  );
  // The moved nodes are the rendered ones, not re-derived text: the argument
  // pair and the tipping factor still read exactly as the card said them.
  assert.deepEqual(
    container.children.flatMap((child) => child.children.map((leaf) => leaf.text)),
    [
      "Both grounds items support the claim text.",
      "The set is implicit; no span was cited.",
      "tipped by: implicit derivation",
      "possible",
    ],
  );

  // The same card, opened. Re-using the input is the purity proof: an
  // in-place transform would have emptied it on the first call.
  const open = collapseAnalysis(card, true);
  const openClasses = open.children.map((child) => child.cls);
  assert.deepEqual(openClasses, [
    "memoria-card-kind",
    "memoria-card-title",
    "memoria-evidence",
    "memoria-block-text",
    "memoria-action-row",
    "memoria-analysis-toggle",
    "memoria-analysis",
  ]);
  assert.equal(open.children[openClasses.indexOf("memoria-analysis-toggle")].text, "Hide analysis");
  assert.equal(card.children.at(-1).cls, "memoria-card-tipped", "the input card is untouched");
});

// The producer state that actually ships: `analysis_fields` writes `tipped_by`
// on every reviewable held row but `argument_for`/`argument_against` have no
// writer yet (V2R-B's declared SPEC GAP), so today's real card has exactly one
// analysis group. A transform fixtured only on the two-group card would pass
// while collapsing nothing on every card the endpoint emits.
test("collapseAnalysis collapses a card whose only analysis is the tipping factor", () => {
  const card = renderBlock({
    kind: "card",
    id: "ev-0022ccdd",
    ref: "projects/project-alpha/draft.md#^blk-c3d4",
    title: "Multi-hop claim",
    kind_line: "evidence-review",
    tipped_by: "multi-hop chain",
    blocks: [
      { kind: "evidence-list", id: "ev-0022ccdd-grounds", items: [] },
      { kind: "text", id: "ev-0022ccdd-routing", text: "Routing: multi-hop" },
    ],
  });

  const collapsed = collapseAnalysis(card, false);
  assert.deepEqual(
    collapsed.children.map((child) => child.cls),
    [
      "memoria-card-kind",
      "memoria-card-title",
      "memoria-evidence",
      "memoria-block-text",
      "memoria-analysis-toggle",
      "memoria-analysis is-collapsed",
    ],
  );
  assert.deepEqual(
    collapsed.children.at(-1).children.map((child) => child.cls),
    ["memoria-card-tipped"],
  );
});

// A permanently blocked row is read-only: no action row, no analysis, and so
// no disclosure control either. A toggle over an empty container would invite
// the PI to open a machine opinion that was never recorded.
test("collapseAnalysis is a no-op for cure cards without analysis", () => {
  const card = renderBlock({
    kind: "card",
    id: "ev-0033eeff",
    ref: "projects/project-alpha/draft.md#^blk-e5f6",
    title: "Drifted claim text",
    kind_line: "evidence-review",
    cure: "repair the draft marker, then re-verify",
    blocks: [
      { kind: "evidence-list", id: "ev-0033eeff-grounds", items: [] },
      { kind: "text", id: "ev-0033eeff-routing", text: "Repair the marker." },
    ],
  });

  assert.deepEqual(
    card.children.map((child) => child.cls),
    ["memoria-card-kind", "memoria-card-title", "memoria-evidence", "memoria-block-text"],
  );
  assert.equal(collapseAnalysis(card, false), card);
  assert.equal(collapseAnalysis(card, true), card);
});

// `memoria-card-meta` is rendered after analysis, so a transform that appends
// the disclosure instead of inserting it at the analysis position would push
// the machine's opinion past the card's own provenance line.
test("collapseAnalysis keeps trailing card meta after the disclosure", () => {
  const card = renderBlock({
    kind: "card",
    id: "ev-0044aabb",
    ref: "projects/project-alpha/draft.md#^blk-a7b8",
    title: "Dated claim",
    kind_line: "evidence-review",
    tipped_by: "implicit derivation",
    raised_by: "verify-project-draft",
    raised_at: "2026-07-16",
    blocks: [{ kind: "text", id: "ev-0044aabb-routing", text: "Routing: implicit" }],
  });

  assert.deepEqual(
    collapseAnalysis(card, false).children.map((child) => child.cls),
    [
      "memoria-card-kind",
      "memoria-card-title",
      "memoria-block-text",
      "memoria-analysis-toggle",
      "memoria-analysis is-collapsed",
      "memoria-card-meta",
    ],
  );
});
