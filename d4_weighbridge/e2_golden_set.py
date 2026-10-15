# e2_golden_set.py — the test weights: counted, versioned, balanced, locked away
import json, hashlib

SET_VERSION = "golden-v3"
WANT = {"real": 140, "edge": 40, "adv": 20}        # real includes the 40 seed failures
WANT_ESCALATE = 35                                 # balanced: should-escalate AND should-not

def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8")]

def fp(text):                                      # same words -> same print, whatever the id
    return hashlib.sha256(" ".join(text.lower().split()).encode()).hexdigest()[:12]

def audit(cases, fewshot, corpus):
    counts = {k: sum(c["slice"] == k for c in cases) for k in WANT}
    assert counts == WANT, f"slice drift: {counts}"
    esc = sum(c["expect"]["decision"] == "escalate" for c in cases)
    assert esc == WANT_ESCALATE, f"balance drift: {esc} should-escalate"
    print(f"{SET_VERSION}: {len(cases)} cases {counts}  escalate {esc} / not {len(cases) - esc}")
    golden = {fp(c["input"]) for c in cases}
    leaks = [e["id"] for e in fewshot if fp(e["input"]) in golden]
    leaks += [d["id"] for d in corpus if fp(d["text"]) in golden]
    print("  leakage:", ", ".join(leaks) if leaks else "none")
    return not leaks

if __name__ == "__main__":
    cases = load("golden_v3.jsonl")
    for fs in ("fewshot_v1_9_sun.jsonl", "fewshot_v1_9_mon.jsonl"):
        ok = audit(cases, load(fs), load("sop_corpus_chunks.jsonl"))
        print(f"  {fs}: GATE", "OPEN" if ok else "SHUT - golden text found outside the vault")
