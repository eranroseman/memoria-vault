// Pure relate-control payload builder (U3 spec section 4). The relation
// roster is server-provided (summary payload `link_relations`, derived from
// the engine's LINK_RELATIONS) so the plugin never grows a second source of
// truth; the plugin validates against — and renders — that roster verbatim.
// The optional free text is emitted as `warrant`, an annotation on the edge
// being written, never as the legacy `reason` alias, which the engine reads as
// the *request's* reason instead.

function buildRelateOperation({ fromPath, relation, toPath, warrant, roster }) {
  const relations = Array.isArray(roster) ? roster : [];
  if (!relations.length) {
    throw new Error("relate: relation roster unavailable — retry after the next poll");
  }
  const source = String(fromPath || "").trim();
  const target = String(toPath || "").trim();
  if (!source) {
    throw new Error("relate: From note is required");
  }
  if (!target) {
    throw new Error("relate: To note is required");
  }
  if (!relations.includes(relation)) {
    throw new Error(`relate: relation must be one of ${relations.join(", ")}`);
  }
  const payload = { source_note_path: source, link_type: relation, target_path: target };
  const warrantText = String(warrant || "").trim();
  if (warrantText) {
    payload.warrant = warrantText;
  }
  return { operationId: "curate-note-link", payload };
}

module.exports = { buildRelateOperation };
