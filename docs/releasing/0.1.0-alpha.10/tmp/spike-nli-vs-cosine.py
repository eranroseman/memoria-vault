#!/usr/bin/env python3
"""Smoke-test whether lexical overlap can distinguish contradiction.

Pass `--models` on a GPU box to run the NLI comparison. No args runs the cheap
self-check and lexical trap.
"""

import re
import sys

TRAP = [
    ("Drug X increases the recovery rate.", "Drug X decreases the recovery rate.", "contradict"),
    ("The method improves accuracy.", "The method reduces accuracy.", "contradict"),
    ("Model A outperforms model B.", "Model B outperforms model A.", "contradict"),
    ("We found no effect of the diet.", "We found a strong effect of the diet.", "contradict"),
]
NEUTRAL = [
    ("The dataset has 8000 examples.", "The dataset has 8000 categories.", "neutral"),
    ("X improves recall.", "X improves precision.", "neutral"),
    ("The drug reduced symptoms in adults.", "The drug reduced symptoms in mice.", "neutral"),
    ("The study ran for 12 weeks.", "The study enrolled 200 patients.", "neutral"),
]


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def jaccard(a, b):
    ta, tb = tokens(a), tokens(b)
    return len(ta & tb) / len(ta | tb) if ta or tb else 0.0


def norm_label(label):
    label = label.lower()
    if label.startswith("contradict"):
        return "contradict"
    if label.startswith("entail"):
        return "entail"
    return "neutral"


def model_run():
    try:
        import torch
        import torch.nn.functional as F
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        print(f"skipped models: {exc}")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pairs = TRAP + NEUTRAL
    for name in [
        "cross-encoder/nli-deberta-v3-small",
        "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
    ]:
        tok = AutoTokenizer.from_pretrained(name)
        model = AutoModelForSequenceClassification.from_pretrained(name).to(device).eval()
        order = [norm_label(model.config.id2label[i]) for i in range(model.config.num_labels)]
        ok = 0
        for premise, hypothesis, gold in pairs:
            with torch.no_grad():
                out = model(**tok(premise, hypothesis, return_tensors="pt", truncation=True).to(device))
            pred = order[int(F.softmax(out.logits[0], -1).argmax())]
            ok += pred == gold
        print(f"{name}: {ok}/{len(pairs)}")


def main():
    assert all(norm_label(g) == g for *_, g in TRAP + NEUTRAL)
    false_same = sum(1 for p, h, _ in TRAP if jaccard(p, h) >= 0.5)
    print(f"lexical false-same contradictions: {false_same}/{len(TRAP)}")
    if "--models" in sys.argv:
        model_run()


if __name__ == "__main__":
    main()

