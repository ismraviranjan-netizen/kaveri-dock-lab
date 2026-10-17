# E5 · The hybrid: the register (keyword) and the foreman (semantic), fused  (objective 3.6 and 3.5, Law 3)
#
#   Register (BM25-ish): rare words count more, repeats saturate, stopwords count nothing. Exact phrases win here.
#   Foreman (semantic):  meaning, not spelling. "parcel stuck, paperwork problem" finds "customs hold".
#                        On battery: a toy, bag-of-words plus a synonym memory, deliberately BLIND to codes and
#                        hyphenated words (like a fuzzy embedding). Live: the model scores each section's relevance.
#   Hybrid:              both scores scaled to 0..1, then weighted. w_sem=1.0 kills the register; 0.0 kills the foreman.
#
# Run on battery:  DRY_RUN=1 python e5_hybrid.py            Run live:  python e5_hybrid.py

import math
import re
from collections import Counter
from common import ask_json, MODEL, SOP, DRY_RUN
from e4_chunking import by_heading

CHUNKS = by_heading(SOP)


# ---------------------------------------------------------------
# STEP 0. The dials and the small vocabularies
# ---------------------------------------------------------------

W_SEM = 0.4                               # weight of the foreman in the fused score
TOP_K = 3

STOP = set("a an the of to and or is in on at for by with what should i do it its this that be".split())
SYN = {"parcel": "consignment", "stuck": "hold", "paperwork": "document", "problem": "mismatch",
       "shipment": "consignment", "goods": "consignment", "customs": "hold"}
STEM = {"re-file": "re-filing", "re-filed": "re-filing", "procedures": "procedure"}


def words(text):
    out = []
    for w in re.findall(r"[a-z0-9\-]+", text.lower()):
        if w not in STOP:
            out.append(STEM.get(w, w))
    return out


def title_of(chunk):
    return chunk.splitlines()[0]          # "[SOP 214 - 4. Re-filing an e-way bill after a hold]"


# ---------------------------------------------------------------
# STEP 1. The register: a keyword score per chunk. Plain Python.
# ---------------------------------------------------------------

def bm25ish(query, chunks):
    docs = [Counter(words(c)) for c in chunks]
    N = len(docs)
    scores = []
    for d in docs:
        s = 0.0
        for q in words(query):
            df = sum(1 for x in docs if q in x)             # how many chunks contain the word
            tf = d[q] / (d[q] + 1.2)                         # saturation: the 9th repeat adds little
            if df:
                s += tf * math.log(1 + (N - df + 0.5) / (df + 0.5))   # rare words count more
        scores.append(s)
    return scores


# ---------------------------------------------------------------
# STEP 2. The foreman: a meaning score per chunk. Toy on battery, the model live.
# ---------------------------------------------------------------

def toy_embed(text):
    bag = Counter()
    for w in words(text):
        if "-" in w or any(ch.isdigit() for ch in w):
            continue                                         # 'e-way', 're-filing', 'kf-2481': unseen by the toy
        bag[SYN.get(w, w)] += 1
    return bag


def cosine(a, b):
    num = sum(a[k] * b[k] for k in a)
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values())) or 1
    return num / den


def semantic(query, chunks):
    if DRY_RUN:
        q = toy_embed(query)
        return [cosine(q, toy_embed(c)) for c in chunks]

    # Live: one call. The model scores every section title against the query, 0 to 10. This is a stand-in
    # for an embedding model plus cosine similarity: same job (meaning, not spelling), one round-trip.
    titles = [title_of(c) for c in chunks]
    question = (
        "Score each section of SOP 214 for how well it answers this query, 0 (irrelevant) to 10 (exactly this). "
        "Reply with JSON only: a list of numbers in the same order as the sections.\n\n"
        "Query: " + query + "\n\nSections:\n" + "\n".join(str(i) + ". " + t for i, t in enumerate(titles, 1))
    )
    scores = ask_json(MODEL, question)
    return [float(s) / 10.0 for s in scores]


# ---------------------------------------------------------------
# STEP 3. The fusion. Scale each side to 0..1, weight, sort, keep the top k.
# ---------------------------------------------------------------

def norm(xs):
    m = max(xs) or 1
    return [x / m for x in xs]


def hybrid(query, chunks, w_sem=W_SEM, k=TOP_K):
    kw = norm(bm25ish(query, chunks))
    sem = norm(semantic(query, chunks))
    fused = [(1 - w_sem) * a + w_sem * b for a, b in zip(kw, sem)]
    order = sorted(range(len(chunks)), key=lambda i: -fused[i])
    return [title_of(chunks[i]) for i in order[:k]]


if __name__ == "__main__":
    print("# E5 · hybrid · " + ("DRY_RUN (toy foreman)" if DRY_RUN else "LIVE foreman · " + MODEL)
          + " · w_sem=" + str(W_SEM))

    # STEP 4. Two queries: one exact phrase, one symptom in the customer's words.
    for q in ("e-way bill re-filing", "parcel stuck, paperwork problem, what should I do"):
        print()
        print("q:", q)
        print("  register only :", hybrid(q, CHUNKS, w_sem=0.0))
        print("  foreman only  :", hybrid(q, CHUNKS, w_sem=1.0))
        print("  hybrid        :", hybrid(q, CHUNKS))
