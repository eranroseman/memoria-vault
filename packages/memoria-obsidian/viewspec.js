// Pure view-spec.v1 rendering (U3 spec section 2): blocks become plain
// {tag, cls, text, attrs, children} trees; only materialize() touches a DOM
// API, and it takes the parent element as an argument. Loudness is rendered
// verbatim from the payload — never invented. Unknown kinds fail visible.

const VIEW_SPEC_VERSION = "view-spec.v1";
const KNOWN_BLOCK_KINDS = ["card", "text", "badge", "action-row", "evidence-list"];
const LOUDNESS_RANK = { block: 0, alert: 1, notice: 2, quiet: 3 };

function node(tag, cls, text, children, attrs) {
  return { tag, cls: cls || "", text: text || "", children: children || [], attrs: attrs || {} };
}

function loudnessClass(block) {
  const value = String(block.loudness || "");
  return value ? ` memoria-loudness-${value}` : "";
}

function unknownBlock(block) {
  return node("div", "memoria-block-unknown", `Unknown block type: ${String(block && block.kind)}`, [
    node("pre", "memoria-block-unknown-raw", JSON.stringify(block)),
  ]);
}

function renderBlock(block) {
  if (!block || typeof block !== "object") {
    return unknownBlock(block);
  }
  switch (block.kind) {
    case "text":
      return node("p", "memoria-block-text", String(block.text || ""));
    case "badge":
      return node("span", `memoria-badge${loudnessClass(block)}`, String(block.label || ""));
    case "evidence-list":
      return node(
        "div",
        "memoria-evidence",
        "",
        (block.items || []).map((item) =>
          node("a", "memoria-evidence-link", String(item.label || item.ref || ""), [], {
            "data-ref": String(item.ref || ""),
          }),
        ),
      );
    case "action-row":
      return node(
        "div",
        "memoria-action-row",
        "",
        (block.actions || []).map((action) =>
          node(
            "button",
            action.primary ? "memoria-action memoria-action-primary" : "memoria-action",
            String(action.label || ""),
            [],
            {
              "data-operation-id": String(action.operation_id || ""),
              "data-payload": JSON.stringify(action.payload || {}),
            },
          ),
        ),
      );
    case "card":
      return renderCard(block);
    default:
      return unknownBlock(block);
  }
}

function renderCard(block) {
  const semanticChildren = (Array.isArray(block.blocks) ? block.blocks : []).map(renderBlock);
  const analysis = [];
  const argumentNodes = [];
  if (block.argument_for) {
    argumentNodes.push(node("span", "memoria-card-for", String(block.argument_for)));
  }
  if (block.argument_against) {
    argumentNodes.push(node("span", "memoria-card-against", String(block.argument_against)));
  }
  if (argumentNodes.length) {
    analysis.push(node("div", "memoria-card-arguments", "", argumentNodes));
  }
  const tipping = [];
  if (block.tipped_by) {
    tipping.push(node("span", "memoria-card-tipped-label", "tipped by: " + String(block.tipped_by)));
  }
  if (block.certainty) {
    tipping.push(node("span", "memoria-certainty-chip", String(block.certainty)));
  }
  if (tipping.length) {
    analysis.push(node("div", "memoria-card-tipped", "", tipping));
  }
  const raisedBy = String(block.raised_by || "");
  const raisedAt = String(block.raised_at || "");
  const meta = [raisedBy ? "raised by " + raisedBy : "", raisedAt].filter(Boolean).join(" · ");
  return node(
    "div",
    "memoria-card" + loudnessClass(block),
    "",
    [
      node("div", "memoria-card-kind" + loudnessClass(block), String(block.kind_line || "")),
      node("div", "memoria-card-title", String(block.title || "")),
      ...semanticChildren,
      ...analysis,
      ...(meta ? [node("div", "memoria-card-meta", meta)] : []),
    ],
    { "data-ref": String(block.ref || "") },
  );
}

function renderView(view) {
  if (!view || view.version !== VIEW_SPEC_VERSION) {
    return [
      node(
        "div",
        "memoria-block-unknown",
        `Unknown view-spec version: ${String(view && view.version)}`,
      ),
    ];
  }
  return (view.blocks || []).map(renderBlock);
}

function sortCards(cards) {
  // `block` needs no separate pin: LOUDNESS_RANK already ranks it first, and an
  // unrecognized band ranks after every known one.
  const rank = (card) => {
    const value = LOUDNESS_RANK[String(card.loudness || "")];
    return value === undefined ? LOUDNESS_RANK.quiet + 1 : value;
  };
  // A negative `age_s` is a hand-edited future `created`, not a card younger
  // than today's. Clamping it to the same 0 an undated card gets makes this
  // order identical to the engine's, which sorts on the full `created` string:
  // equal ages then fall back to the payload order the engine already chose.
  const age = (card) => Math.max(0, Number(card.age_s) || 0);
  return [...cards].sort((a, b) => {
    if (rank(a) !== rank(b)) {
      return rank(a) - rank(b);
    }
    return age(b) - age(a);
  });
}

// V2 spec section 3: evidence first, machine analysis behind an explicit
// disclosure. Structural, not stylistic — the analysis nodes move to the
// position after every semantic child, so no stylesheet decides reading order.
const ANALYSIS_CLASSES = ["memoria-card-arguments", "memoria-card-tipped"];

function collapseAnalysis(tree, open) {
  const isAnalysis = (child) => ANALYSIS_CLASSES.includes(child.cls);
  const moved = tree.children.filter(isAnalysis);
  // A read-only cure card records no analysis, so it gets no control: a toggle
  // over an empty container offers a machine opinion that was never written.
  if (!moved.length) {
    return tree;
  }
  const children = [];
  let disclosed = false;
  for (const child of tree.children) {
    if (!isAnalysis(child)) {
      children.push(child);
      continue;
    }
    // Every analysis child collapses into the one container, which takes the
    // place of the first of them — so a trailing `memoria-card-meta` stays
    // last, and the disclosure never floats above the evidence.
    if (disclosed) {
      continue;
    }
    disclosed = true;
    children.push(
      node(
        "button",
        "memoria-analysis-toggle",
        open ? "Hide analysis" : "Show analysis (machine)",
        [],
        { "data-toggle-analysis": "1" },
      ),
      node("div", open ? "memoria-analysis" : "memoria-analysis is-collapsed", "", moved),
    );
  }
  return { ...tree, children };
}

function moveSelection(count, index, key) {
  if (!count) {
    return 0;
  }
  if (key === "j") {
    return Math.min(count - 1, index + 1);
  }
  if (key === "k") {
    return Math.max(0, index - 1);
  }
  return index;
}

function materialize(tree, parentEl) {
  const el = parentEl.createEl(tree.tag, {
    cls: tree.cls || undefined,
    text: tree.text || undefined,
  });
  for (const [key, value] of Object.entries(tree.attrs || {})) {
    el.setAttribute(key, value);
  }
  for (const child of tree.children || []) {
    materialize(child, el);
  }
  return el;
}

module.exports = {
  KNOWN_BLOCK_KINDS,
  LOUDNESS_RANK,
  VIEW_SPEC_VERSION,
  collapseAnalysis,
  materialize,
  moveSelection,
  renderBlock,
  renderView,
  sortCards,
};
