#!/usr/bin/env python3
"""§0 NLI/HANS spike — does a local NLI comparator actually beat cosine on the
lexical-overlap blind spot, and does it fit beside qwen2.5:7b on 16 GB?

Run order of laziness:
  python3 spike-nli-vs-cosine.py            # no deps: lexical-trap demo + self-check (runs anywhere)
  python3 spike-nli-vs-cosine.py --models   # adds the real NLI vs sentence-cosine run (needs the GPU box)

The fixture is the point: high-token-overlap pairs whose meaning is the OPPOSITE
(contradiction) or merely DIFFERENT. A similarity method that scores them "same"
has the blind spot §3.1 warns about. NLI must clear them to earn its place.
ponytail: hand fixture of 16 pairs, not a benchmark harness — enough to answer go/no-go.
"""
import re, sys

# (premise, hypothesis, gold, lexical_trap)  gold ∈ entail|contradict|neutral
FIXTURE = [
    ("Drug X increases the recovery rate.",            "Drug X decreases the recovery rate.",            "contradict", True),
    ("The method improves accuracy on small datasets.","The method reduces accuracy on small datasets.", "contradict", True),
    ("Model A outperforms model B.",                   "Model B outperforms model A.",                   "contradict", True),
    ("The sample size was sufficient for significance.","The sample size was insufficient for significance.","contradict", True),
    ("Cosine similarity collapses on reasoning relevance.","Cosine similarity excels at reasoning relevance.","contradict", True),
    ("We found no effect of the diet on weight.",      "We found a strong effect of the diet on weight.","contradict", True),
    ("The dataset has 8000 labeled examples.",         "The dataset has 8000 distinct categories.",      "neutral",    True),
    ("Results held for adults but not for children.",  "Results held for children but not for adults.",  "contradict", True),
    ("The treatment was effective in the trials.",     "The treatment worked in the trials.",            "entail",     True),
    ("Accuracy rose after fine-tuning the model.",     "Fine-tuning the model raised its accuracy.",     "entail",     True),
    ("The intervention lowered mortality.",            "Fewer patients died after the intervention.",    "entail",     False),
    ("Retrieval quality drives grounded output.",      "Grounded output depends on how good retrieval is.","entail",   False),
    ("X significantly improves Y.",                    "X significantly improves Y.",                    "entail",     False),
    ("The encoder was frozen during training.",        "Bananas are a good source of potassium.",        "neutral",    False),
    ("The gate routes uncertain items to the PI.",     "Uncertain items are escalated to the researcher.","entail",     False),
    ("Self-consistency is a reliable confidence signal.","Self-consistency is not a reliable confidence signal.","contradict", True),
]

_tok = lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))

def jaccard(a, b):
    ta, tb = _tok(a), _tok(b)
    return len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0


def lexical_demo(thresh=0.5):
    """A token-overlap 'same?' classifier — the cheapest lexical method. Show it
    cannot tell contradiction from entailment when overlap is high."""
    rows = [(p, h, g, trap, jaccard(p, h)) for p, h, g, trap in FIXTURE]
    traps = [r for r in rows if r[3]]
    # a trap-contradiction scored above threshold = mistaken for "same/compatible"
    false_same = [r for r in traps if r[2] == "contradict" and r[4] >= thresh]
    print(f"  lexical 'same?' threshold = {thresh}")
    print(f"  trap-contradiction pairs:        {sum(1 for r in traps if r[2]=='contradict')}")
    print(f"  …scored ≥{thresh} (FALSE 'same'): {len(false_same)}   <- the blind spot")
    print(f"  mean Jaccard  contradiction={_mean([r[4] for r in rows if r[2]=='contradict']):.2f}"
          f"  entailment={_mean([r[4] for r in rows if r[2]=='entail']):.2f}"
          f"  (high+similar => lexical can't separate them)")
    return false_same

_mean = lambda xs: sum(xs) / len(xs) if xs else 0.0


def model_run():
    """Real NLI vs sentence-cosine. Needs transformers + a local NLI model and
    sentence-transformers. Run on the 16 GB box; reports accuracy + VRAM."""
    try:
        import torch
        from sentence_transformers import SentenceTransformer, util, CrossEncoder
    except ImportError as e:
        print(f"  skipped: {e}. pip install torch sentence-transformers, then --models on the GPU box.")
        return
    nli = CrossEncoder("cross-encoder/nli-deberta-v3-small")        # ~140M, label order: contradiction, entailment, neutral
    emb = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    label = ["contradict", "entail", "neutral"]
    nli_ok = cos_false_same = 0
    for p, h, g, trap in FIXTURE:
        pred = label[int(nli.predict([(p, h)]).argmax())]
        nli_ok += pred == g
        cos = float(util.cos_sim(emb.encode(p), emb.encode(h)))
        if g == "contradict" and cos >= 0.5:
            cos_false_same += 1
        print(f"  [{'ok' if pred==g else 'XX'}] nli={pred:<10} cos={cos:+.2f} gold={g:<10} trap={trap}  {p[:38]}")
    n_contra = sum(1 for _p, _h, g, _t in FIXTURE if g == "contradict")
    print(f"\n  NLI accuracy: {nli_ok}/{len(FIXTURE)}")
    print(f"  cosine FALSE 'same' on contradictions (≥0.5): {cos_false_same}/{n_contra}  <- the blind spot NLI must beat")
    if torch.cuda.is_available():
        print(f"  peak VRAM both models: {torch.cuda.max_memory_allocated()/1e9:.2f} GB "
              f"(qwen2.5:7b ~5 GB Q4 → headroom on 16 GB; verdict: {'FITS' if torch.cuda.max_memory_allocated()/1e9 < 8 else 'TIGHT'})")


def self_check():
    assert len(FIXTURE) >= 12
    assert all(g in ("entail", "contradict", "neutral") for _p, _h, g, _t in FIXTURE)
    # the fixture must actually contain the trap: ≥3 high-overlap contradictions
    traps_contra = [(p, h) for p, h, g, t in FIXTURE if t and g == "contradict" and jaccard(p, h) >= 0.5]
    assert len(traps_contra) >= 3, "fixture doesn't trap a lexical method — not a useful spike"
    # paraphrase with LOW overlap must exist (where embeddings should beat lexical)
    assert any(g == "entail" and jaccard(p, h) < 0.4 for p, h, g, _ in FIXTURE)
    print("self-check: OK (fixture is well-formed and actually traps lexical similarity)")


if __name__ == "__main__":
    self_check()
    print("\nLexical-trap demonstration (no model needed):")
    lexical_demo()
    print("\nModel run:")
    model_run() if "--models" in sys.argv else print("  (pass --models on the GPU box for the real NLI vs cosine numbers)")
