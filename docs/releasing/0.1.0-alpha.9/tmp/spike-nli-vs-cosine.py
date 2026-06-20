#!/usr/bin/env python3
"""§0 NLI spike — does a local NLI comparator earn §3.1's "replace cosine" call?

Run order of laziness:
  python3 spike-nli-vs-cosine.py            # no deps: lexical-trap demo + self-check (runs anywhere)
  python3 spike-nli-vs-cosine.py --models   # adds the real NLI runs (needs torch + transformers + a GPU)

RESULTS (alpha.9, on the RTX 4060 Ti, both models <0.6 GB VRAM — fit is a non-issue):

  TRAP fixture (high overlap, relationship flips e.g. increases/decreases):
    cosine (all-MiniLM)                  : 0/8  (scores all 8 contradictions "same", 0.78-1.00)
    nli-deberta-v3-small                 : 8/8
    DeBERTa-v3-base-mnli-fever-anli      : 8/8     -> NLI clears the easy trap; NOT HANS-fooled here.

  NEUTRAL fixture (same topic, DIFFERENT variable/population/metric — the real common case):
    nli-deberta-v3-small                 : 6/12, and WRONG answers are CONFIDENT (0.97-1.00)
    DeBERTa-v3-base-mnli-fever-anli      : 8/12, still confidently wrong on several (0.94-0.98)

  Verdict: NLI confidently MINTS FALSE CONTRADICTIONS between merely-different claims, and a
  confidence threshold cannot filter them. So NLI gives the relationship verdict only; a
  contradiction edge must also require variable/context MATCH from the structured-claim schema
  (§3.3) — that schema is a precondition for §3.1, not an enhancement. Prefer the ANLI/FEVER
  model (better neutral); contradiction direction is stable (0 flips). Re-run on real vault
  claim pairs (current-state-baseline.md) before committing.
ponytail: two hand fixtures, ~20 pairs — a smoke test that answers go/no-go, not a benchmark.
"""

import re
import sys

# (premise, hypothesis, gold) — gold in entail|contradict|neutral
TRAP = [  # high token overlap, opposite/different meaning — the cosine trap
    ("Drug X increases the recovery rate.", "Drug X decreases the recovery rate.", "contradict"),
    ("The method improves accuracy on small datasets.", "The method reduces accuracy on small datasets.", "contradict"),
    ("Model A outperforms model B.", "Model B outperforms model A.", "contradict"),
    ("The sample size was sufficient for significance.", "The sample size was insufficient for significance.", "contradict"),
    ("Cosine similarity collapses on reasoning relevance.", "Cosine similarity excels at reasoning relevance.", "contradict"),
    ("We found no effect of the diet on weight.", "We found a strong effect of the diet on weight.", "contradict"),
    ("Results held for adults but not for children.", "Results held for children but not for adults.", "contradict"),
    ("Self-consistency is a reliable confidence signal.", "Self-consistency is not a reliable confidence signal.", "contradict"),
]
NEUTRAL = [  # same topic, DIFFERENT variable — must be neutral, not contradiction
    ("The dataset has 8000 labeled examples.", "The dataset has 8000 distinct categories.", "neutral"),
    ("Method A uses an attention mechanism.", "Method A uses a convolutional mechanism.", "neutral"),
    ("The study ran for 12 weeks.", "The study enrolled 200 patients.", "neutral"),
    ("X improves recall.", "X improves precision.", "neutral"),
    ("The model was trained on English text.", "The model was evaluated on English text.", "neutral"),
    ("Results were significant at p<0.05.", "Results were significant at p<0.01.", "neutral"),
    ("The drug reduced symptoms in adults.", "The drug reduced symptoms in mice.", "neutral"),
    ("The study ran for 12 weeks.", "The study ran for twelve weeks.", "entail"),
    ("The treatment was effective in trials.", "The treatment worked in trials.", "entail"),
    ("The intervention lowered mortality.", "Fewer patients died after the intervention.", "entail"),
    ("Drug X increases recovery.", "Drug X decreases recovery.", "contradict"),
    ("The method improves accuracy.", "The method does not improve accuracy.", "contradict"),
]
FIXTURE = TRAP  # back-compat for importers; the lexical demo runs on the trap set


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def jaccard(a, b):
    ta, tb = tokens(a), tokens(b)
    return len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def norm_label(lbl):
    low = lbl.lower()
    if low.startswith("contradict"):
        return "contradict"
    if low.startswith("entail"):
        return "entail"
    return "neutral"


def lexical_demo(thresh=0.5):
    """Token-overlap 'same?' classifier — show it can't separate contradiction from entailment."""
    false_same = [(p, h) for p, h, g in TRAP if g == "contradict" and jaccard(p, h) >= thresh]
    contra = [jaccard(p, h) for p, h, g in TRAP if g == "contradict"]
    print(f"  trap contradictions scored >={thresh} as 'same' (FALSE): {len(false_same)}/{len(TRAP)}  <- blind spot")
    print(f"  mean Jaccard contradiction={mean(contra):.2f}  (overlap is HIGH on the pairs that mean the opposite)")


def model_run():
    try:
        import torch
        import torch.nn.functional as F
        from sentence_transformers import SentenceTransformer, util
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as e:
        print(f"  skipped: {e}. pip install torch transformers sentence-transformers (GPU box).")
        return
    dev = "cuda" if torch.cuda.is_available() else "cpu"

    def eval_nli(name, pairs):
        if dev == "cuda":
            torch.cuda.reset_peak_memory_stats()
        tok = AutoTokenizer.from_pretrained(name)
        mdl = AutoModelForSequenceClassification.from_pretrained(name).to(dev).eval()
        order = [norm_label(mdl.config.id2label[i]) for i in range(mdl.config.num_labels)]  # NEVER hardcode this

        def predict(p, h):
            with torch.no_grad():
                pr = F.softmax(mdl(**tok(p, h, return_tensors="pt", truncation=True).to(dev)).logits[0], -1)
            i = int(pr.argmax())
            return order[i], float(pr[i])

        ok, wrong_conf, flips = 0, [], 0
        for p, h, g in pairs:
            lab, c = predict(p, h)
            ok += lab == g
            if lab != g:
                wrong_conf.append(round(c, 2))
            if g == "contradict" and predict(h, p)[0] != lab:
                flips += 1
        vram = torch.cuda.max_memory_allocated() / 1e9 if dev == "cuda" else 0.0
        del mdl
        if dev == "cuda":
            torch.cuda.empty_cache()
        print(f"    {name.split('/')[-1]:<34} acc {ok}/{len(pairs)}  "
              f"wrong-conf {wrong_conf or '[]'}  contra-dir-flips {flips}  VRAM {vram:.2f} GB")

    models = ["cross-encoder/nli-deberta-v3-small", "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"]
    print("\n  TRAP fixture (relationship flips, variables identical):")
    for m in models:
        eval_nli(m, TRAP)
    print("  NEUTRAL fixture (same topic, different variable — the dangerous case):")
    for m in models:
        eval_nli(m, NEUTRAL)

    emb = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=dev)
    n_contra = sum(1 for *_, g in TRAP if g == "contradict")
    fs = sum(1 for p, h, g in TRAP if g == "contradict" and float(util.cos_sim(emb.encode(p), emb.encode(h))) >= 0.5)
    print(f"  cosine baseline: {fs}/{n_contra} trap contradictions called 'same'")


def self_check():
    assert len(TRAP) >= 6 and len(NEUTRAL) >= 8
    assert all(norm_label(g) == g for *_, g in TRAP + NEUTRAL)
    traps = [(p, h) for p, h, g in TRAP if g == "contradict" and jaccard(p, h) >= 0.5]
    assert len(traps) >= 3, "trap fixture doesn't actually trap a lexical method"
    print("self-check: OK")


if __name__ == "__main__":
    self_check()
    print("\nLexical-trap demonstration (no model needed):")
    lexical_demo()
    print("\nModel run:")
    model_run() if "--models" in sys.argv else print("  (pass --models on a GPU box for the real numbers)")
