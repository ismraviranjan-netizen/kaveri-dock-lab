# E5 · The hybrid — the register (keyword) and the toy foreman (semantic) (objective 3.6 / 3.5)
import math, os, re
from collections import Counter
from e4_chunking import by_heading, doc

CHUNKS = by_heading(doc)
STOP = set("a an the of to and or is in on at for by with what should i do it its this that be".split())
SYN = {"parcel": "consignment", "stuck": "hold", "paperwork": "document", "problem": "mismatch",
       "shipment": "consignment", "goods": "consignment", "customs": "hold"}

STEM = {"re-file": "re-filing", "re-filed": "re-filing", "procedures": "procedure"}

def words(t):
    return [STEM.get(w, w) for w in re.findall(r"[a-z0-9\-]+", t.lower()) if w not in STOP]

def bm25ish(query, chunks):                       # the register: rare words count more, repeats saturate
    docs = [Counter(words(c)) for c in chunks]
    N = len(docs)
    scores = []
    for d in docs:
        s = 0.0
        for q in words(query):
            df = sum(1 for x in docs if q in x)
            tf = d[q] / (d[q] + 1.2)                       # saturation: the 9th repeat adds little
            if df: s += tf * math.log(1 + (N - df + .5) / (df + .5))
        scores.append(s)
    return scores

def toy_embed(t):                                  # the foreman: meaning via synonyms, blind to codes
    bag = Counter()
    for w in words(t):
        if "-" in w or any(ch.isdigit() for ch in w): continue   # 'e-way', 're-filing', 'kf-2481' unseen
        bag[SYN.get(w, w)] += 1
    return bag

def cosine(a, b):
    num = sum(a[k] * b[k] for k in a)
    den = math.sqrt(sum(v*v for v in a.values())) * math.sqrt(sum(v*v for v in b.values())) or 1
    return num / den

def semantic(query, chunks):
    if not os.getenv("DRY_RUN"):
        raise SystemExit("real_embed is the paid path: set DRY_RUN=1 for the toy foreman")
    q = toy_embed(query)
    return [cosine(q, toy_embed(c)) for c in chunks]

def norm(xs):
    m = max(xs) or 1
    return [x / m for x in xs]

def hybrid(query, chunks, w_sem=0.4, k=3):
    kw, sem = norm(bm25ish(query, chunks)), norm(semantic(query, chunks))
    fused = [(1 - w_sem) * a + w_sem * b for a, b in zip(kw, sem)]
    top = sorted(range(len(chunks)), key=lambda i: -fused[i])[:k]
    return [chunks[i].splitlines()[0] for i in top]

if __name__ == "__main__":
    for q in ("e-way bill re-filing", "parcel stuck, paperwork problem, what should I do"):
        print("q:", q)
        print(hybrid(q, CHUNKS))
