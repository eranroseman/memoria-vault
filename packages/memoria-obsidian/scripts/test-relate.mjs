import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { buildRelateOperation } = require("../src/relate.js");

const roster = ["contradicts", "extends", "qualifier", "rebuttal", "supports", "warrant"];

test("builds a curate-note-link enqueue with a rebuttal and warrant annotation", () => {
  assert.deepEqual(
    buildRelateOperation({
      fromPath: "notes/a.md",
      relation: "rebuttal",
      toPath: "notes/b.md",
      warrant: "  B replicates A's cohort.  ",
      roster,
    }),
    {
      operationId: "curate-note-link",
      payload: {
        source_note_path: "notes/a.md",
        link_type: "rebuttal",
        target_path: "notes/b.md",
        warrant: "B replicates A's cohort.",
      },
    },
  );
});

test("omits warrant when the warrant text is blank", () => {
  const operation = buildRelateOperation({
    fromPath: "notes/a.md",
    relation: "warrant",
    toPath: "notes/b.md",
    warrant: "   ",
    roster,
  });
  assert.ok(!("warrant" in operation.payload));
});

test("rejects missing endpoints and off-roster relations", () => {
  assert.throws(
    () => buildRelateOperation({ fromPath: "", relation: "supports", toPath: "b", roster }),
    /relate: From note is required/,
  );
  assert.throws(
    () => buildRelateOperation({ fromPath: "a", relation: "supports", toPath: "", roster }),
    /relate: To note is required/,
  );
  assert.throws(
    () => buildRelateOperation({ fromPath: "a", relation: "refutes", toPath: "b", roster }),
    /relate: relation must be one of contradicts, extends, qualifier, rebuttal, supports, warrant/,
  );
  assert.throws(
    () => buildRelateOperation({ fromPath: "a", relation: "supports", toPath: "b", roster: [] }),
    /relate: relation roster unavailable/,
  );
});

// The two senses of the word are independent (U3-PLUG cross-section contract
// 12): a `warrant` *relation* links a license note, while Warrant *text*
// annotates whichever edge was selected. The test above pairs the relation with
// blank text and the first one pairs text with a different relation, so nothing
// yet forbids a builder that treats the relation as the text's owner -- routing
// the annotation elsewhere, or dropping it, exactly when the two coincide.
test("a warrant relation and Warrant text are carried independently", () => {
  assert.deepEqual(
    buildRelateOperation({
      fromPath: "notes/a.md",
      relation: "warrant",
      toPath: "notes/license.md",
      warrant: "Cohort licensing rule.",
      roster,
    }).payload,
    {
      source_note_path: "notes/a.md",
      link_type: "warrant",
      target_path: "notes/license.md",
      warrant: "Cohort licensing rule.",
    },
  );
});

// Producer state: a caller that omits a field entirely rather than passing an
// empty string -- the modal's Warrant textarea is never touched, or a From/To
// binding is read before it is set. `String(undefined)` is the *five-character
// string* "undefined", so dropping a `|| ""` does not fail these open: it
// submits the literal word as a vault path or hangs it on the edge as the PI's
// warrant.
test('absent fields are refused or omitted, never the string "undefined"', () => {
  assert.throws(
    () => buildRelateOperation({ relation: "supports", toPath: "notes/b.md", roster }),
    /relate: From note is required/,
  );
  assert.throws(
    () => buildRelateOperation({ fromPath: "notes/a.md", relation: "supports", roster }),
    /relate: To note is required/,
  );
  for (const warrant of [undefined, null]) {
    const operation = buildRelateOperation({
      fromPath: "notes/a.md",
      relation: "supports",
      toPath: "notes/b.md",
      warrant,
      roster,
    });
    assert.deepEqual(operation.payload, {
      source_note_path: "notes/a.md",
      link_type: "supports",
      target_path: "notes/b.md",
    });
  }
});

// Producer state: the picker returns a path the PI pasted with surrounding
// space, and the textarea keeps the newline the PI typed after the sentence.
// Trimming has to happen before the required-field check as well as before the
// payload is built, or a space-only endpoint ships as a nonempty path the
// engine then refuses with a file-not-found the PI cannot act on.
test("endpoints and warrant text are trimmed, and a blank-but-nonempty endpoint is refused", () => {
  assert.deepEqual(
    buildRelateOperation({
      fromPath: "  notes/a.md ",
      relation: "extends",
      toPath: "\tnotes/b.md\n",
      warrant: "Same instrument.\n",
      roster,
    }).payload,
    {
      source_note_path: "notes/a.md",
      link_type: "extends",
      target_path: "notes/b.md",
      warrant: "Same instrument.",
    },
  );
  assert.throws(
    () => buildRelateOperation({ fromPath: "   ", relation: "supports", toPath: "b", roster }),
    /relate: From note is required/,
  );
  assert.throws(
    () => buildRelateOperation({ fromPath: "a", relation: "supports", toPath: "\t\n", roster }),
    /relate: To note is required/,
  );
});

// The roster is the server's, so the gate has to be exact membership over an
// actual list. A string roster is the case with teeth: `"supports"` has a
// truthy `.length` and its `.includes` is a *substring* test, so without the
// array check a served scalar would silently admit `"support"` -- an off-roster
// relation the engine refuses only at the frontmatter layer, after the request
// is journaled.
test("the roster gate refuses a non-list roster and matches verbs exactly", () => {
  for (const unloaded of [undefined, null, "supports", 6]) {
    assert.throws(
      () =>
        buildRelateOperation({
          fromPath: "a",
          relation: "support",
          toPath: "b",
          roster: unloaded,
        }),
      /relate: relation roster unavailable/,
    );
  }
  for (const inexact of ["support", "supportss", "SUPPORTS", ""]) {
    assert.throws(
      () => buildRelateOperation({ fromPath: "a", relation: inexact, toPath: "b", roster }),
      /relate: relation must be one of contradicts, extends, qualifier, rebuttal, supports, warrant/,
    );
  }
});
