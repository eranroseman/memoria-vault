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
  const arguments = [];
  if (block.argument_for) {
    arguments.push(node("span", "memoria-card-for", String(block.argument_for)));
  }
  if (block.argument_against) {
    arguments.push(node("span", "memoria-card-against", String(block.argument_against)));
  }
  if (arguments.length) {
    analysis.push(node("div", "memoria-card-arguments", "", arguments));
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
  return [...cards].sort((a, b) => {
    if (rank(a) !== rank(b)) {
      return rank(a) - rank(b);
    }
    return (Number(b.age_s) || 0) - (Number(a.age_s) || 0);
  });
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
  materialize,
  moveSelection,
  renderBlock,
  renderView,
  sortCards,
};
