"""L1 component test for extract — extracted from its former --self-test (ADR-44)."""
import extract as _m

globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_extract():
    def _run():
        good = ("This is a perfectly ordinary paragraph of English prose describing a "
                "study, its methods, and the results obtained over a long evaluation. ") * 6
        garbled = "�� ab � cd � " * 80
        tiny = "short."
        checks = [
            ("coherent prose -> ok", coherence(good, pages=1)["ok"]),
            ("garbled -> not ok (garbled)", coherence(garbled, pages=1)["reason"] == "garbled"),
            ("tiny -> not ok (too-few-chars)", coherence(tiny, pages=1)["reason"] == "too-few-chars"),
            ("empty -> not ok (empty)", coherence("", pages=1)["reason"] == "empty"),
            ("no source & no pdf -> degraded", extract({}, None)["degraded"] is True
             and extract({}, None)["source"] == "none"),
            ("missing pdf path -> from_pdf no-pdf", from_pdf(Path("/no/such.pdf"))[1] == "no-pdf"),
        ]
        # ADR-30: a malformed PDF is parsed in the resource-limited subprocess and
        # degrades gracefully (the parent never crashes) — note moves past "no-pdf".
        _bad_pdf = Path(tempfile.gettempdir()) / "memoria-extract-selftest.pdf"
        _bad_pdf.write_bytes(b"%PDF-1.4 not a real pdf\n")
        try:
            _txt, _note = from_pdf(_bad_pdf)
            checks.append(("garbage pdf -> sandboxed + handled, no crash", _note != "no-pdf"))
        finally:
            _bad_pdf.unlink(missing_ok=True)
        bad = [n for n, ok in checks if not ok]
        for n, ok in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {n}")
        print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: extract.py self-test")
        return 1 if bad else 0
    assert _run() == 0


def test_pmc_api_key_param():
    """NCBI api_key is sent iff provided (10 req/s vs 3 — E-utilities keying)."""
    captured = {}

    def _fake_get(url, *a, **k):
        captured["url"] = url
        return None

    orig = _m._get
    _m._get = _fake_get
    try:
        _m.from_pmc("PMC123", email="a@b.c", api_key="K")
        assert "api_key=K" in captured["url"]
        _m.from_pmc("PMC123", email="a@b.c")
        assert "api_key" not in captured["url"]
    finally:
        _m._get = orig


def test_unpaywall_is_first_and_falls_back(monkeypatch):
    calls = []
    good = ("This open access PDF has a clean text layer and enough ordinary "
            "English prose to pass the deterministic coherence gate. ") * 6

    monkeypatch.setattr(_m, "from_unpaywall",
                        lambda ids, email="": calls.append("unpaywall") or (good, "pymupdf4llm", "https://oa/pdf"))
    monkeypatch.setattr(_m, "from_pmc",
                        lambda pmcid, email="", api_key="": calls.append("pmc") or "SHOULD NOT RUN")
    got = _m.extract({"doi": "10.1/x", "pmcid": "PMC1"}, None, "pi@example.test")
    assert got["source"] == "unpaywall"
    assert got["pdf_url"] == "https://oa/pdf"
    assert calls == ["unpaywall"]

    calls.clear()
    pmc_text = ("PMC full text is coherent and remains the fallback after "
                "an unusable Unpaywall PDF. ") * 7
    monkeypatch.setattr(_m, "from_unpaywall",
                        lambda ids, email="": calls.append("unpaywall") or ("tiny", "pymupdf4llm", "https://oa/bad"))
    monkeypatch.setattr(_m, "from_pmc",
                        lambda pmcid, email="", api_key="": calls.append("pmc") or pmc_text)
    got = _m.extract({"doi": "10.1/x", "pmcid": "PMC1"}, None, "pi@example.test")
    assert got["source"] == "pmc"
    assert calls == ["unpaywall", "pmc"]
