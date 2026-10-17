# E10 · The two lanes: INGEST (runs weekly) and QUERY (runs 40,000 times a day)  (objectives 3.5, 3.6 · Laws 2, 3)
#
#   The Part 4 drawing, as running code. Read the two lanes as two different clocks:
#
#   INGEST LANE · once per corpus change            QUERY LANE · once per question
#     400 SOPs (here: one, SOP 214)                   dispatcher question
#     chunk on headings            (E4)               BM25 + vector: search BOTH indexes       no model call
#     ★ situate: a model writes a sentence            fuse the two ranked lists -> candidates  no model call
#       of context INTO each chunk   1 model call     rerank the candidates -> top-N           1 model call
#     embed -> vector index          no model call    generate: cached preamble + top-N + q    1 model call
#     index -> BM25 (keyword)        no model call
#
#   The star is situate. The context sentence is written BEFORE both indexes see the chunk, so the register
#   (keyword) and the foreman (meaning) both benefit, and the bill for it is paid once a week, not per question.
#   To make that visible, this file builds the shelves TWICE, plain and situated, and shows where section 4 ranks
#   for a customer's question that never uses the SOP's words.
#
#   Honest labels. The vector index here is E5's toy bag-of-words (the Claude API has no embeddings endpoint);
#   a real desk uses an embedding model. The SHAPE is the lesson: a vector is computed once at ingest and compared
#   40,000 times a day for free. The reranker and the writer are real Fable calls. Live run: 5 calls in all.
#
# Run on battery:  DRY_RUN=1 python e10_two_lanes.py        Run live:  python e10_two_lanes.py

import math
from collections import Counter
from common import create_message, ask_json, text_of, log_line, MODEL, MAX_TOKENS, SOP, DRY_RUN
from e4_chunking import by_heading
from e5_hybrid import words, toy_embed, cosine, title_of

TOP_N = 3                                  # the drawing says top-20 out of ~150 candidates. Ten chunks: top-3 of 10.
RRF_K = 60                                 # the usual constant in reciprocal-rank fusion
QUESTIONS = ("how do I re-file an e-way bill?",                        # the SOP's own words: the register's game
             "parcel stuck, paperwork problem, what should I do")      # the customer's words: the foreman's game


# ===============================================================
# INGEST LANE. Everything in this half runs when the SOPs change, not when a question arrives.
# ===============================================================

# STEP 1. Chunk on headings. E4's cutter: one box per section, the label written inside.
def chunk(sop):
    return by_heading(sop)


# STEP 2. ★ Situate. One model call writes one sentence of context per chunk: which document it is from, what
#         it is about, in words a dispatcher would use. That sentence is glued to the FRONT of the chunk, so
#         every index built afterwards sees it. Paid once per ingest run. On battery: a toy sentence from the title.
def situate(chunks):
    if DRY_RUN:
        return ["This chunk is from SOP 214 (customs holds and e-way bill re-filing) and covers "
                + title_of(c).strip("[]").split(" - ", 1)[-1].lower() + "." for c in chunks]
    numbered = "\n\n".join("CHUNK " + str(i) + ":\n" + c for i, c in enumerate(chunks, 1))
    question = (
        "Below are the " + str(len(chunks)) + " sections of SOP 214, Kaveri Freight's procedure for customs holds "
        "and e-way bill re-filing. For EACH chunk write ONE sentence (under 35 words) that situates it: name the "
        "document, say what the chunk is about, and use the plain words a dispatcher or customer would use for the "
        "same thing (for example 'parcel stuck at customs' as well as 'customs hold'). "
        "Reply with JSON only: a list of " + str(len(chunks)) + " strings, in chunk order.\n\n" + numbered
    )
    return [str(s) for s in ask_json(MODEL, question)]


def with_context(chunks, sentences):
    return [s + "\n" + c for s, c in zip(sentences, chunks)]


# STEP 3. embed -> vector index. One vector per chunk, computed now, stored. Toy here (see the header).
def build_vectors(docs):
    return [toy_embed(d) for d in docs]


# STEP 4. index -> BM25. The register's shelf: per-chunk word counts and, per word, how many chunks hold it.
#         E5 recomputed this on every query. A real index does it once, here, so a query costs a lookup.
def build_bm25(docs):
    tf = [Counter(words(d)) for d in docs]
    df = Counter()
    for counts in tf:
        for w in counts:
            df[w] += 1
    return {"tf": tf, "df": df, "N": len(docs)}


def ingest(sop, situated):
    """The whole top lane. Returns the shelves: the chunks the writer will read, and the two indexes."""
    chunks = chunk(sop)
    sentences = situate(chunks) if situated else [""] * len(chunks)
    docs = with_context(chunks, sentences) if situated else chunks
    return {"chunks": docs, "sentences": sentences, "vectors": build_vectors(docs), "bm25": build_bm25(docs)}


# ===============================================================
# QUERY LANE. Everything in this half runs once per question, 40,000 times a day.
# ===============================================================

# STEP 5. Search BOTH indexes. Two ranked lists of chunk numbers. No model call on either side.
def bm25_search(index, query):
    scores = []
    for counts in index["tf"]:
        s = 0.0
        for q in words(query):
            df = index["df"][q]
            if df:
                tf = counts[q] / (counts[q] + 1.2)
                s += tf * math.log(1 + (index["N"] - df + 0.5) / (df + 0.5))
        scores.append(s)
    return sorted(range(len(scores)), key=lambda i: -scores[i])


def vector_search(vectors, query):
    q = toy_embed(query)
    scores = [cosine(q, v) for v in vectors]
    return sorted(range(len(scores)), key=lambda i: -scores[i])


# STEP 6. Fuse -> candidates. Reciprocal-rank fusion: a chunk earns 1/(60+rank) from each list it appears in.
#         Rank 1 on one list and rank 8 on the other beats rank 4 on both. No scaling, no model, no weights to tune.
def fuse(ranked_lists):
    score = Counter()
    for ranked in ranked_lists:
        for rank, i in enumerate(ranked, 1):
            score[i] += 1.0 / (RRF_K + rank)
    return [i for i, _ in score.most_common()]


# STEP 7. Rerank -> top-N. The one place in the query lane that reads the chunk TEXT against the question.
#         A cross-reading model scores every (question, candidate) pair; the best N go forward. One call.
def rerank(question, chunks, candidates):
    if DRY_RUN:
        return candidates[:TOP_N]
    listing = "\n\n".join("CANDIDATE " + str(n) + ":\n" + chunks[i] for n, i in enumerate(candidates, 1))
    prompt = ("Score each candidate chunk 0 (useless) to 10 (answers it exactly) for THIS question. Judge by the "
              "chunk text, not the title. Reply with JSON only: a list of " + str(len(candidates)) + " numbers in "
              "candidate order.\n\nQuestion: " + question + "\n\n" + listing)
    scores = [float(s) for s in ask_json(MODEL, prompt)]
    order = sorted(range(len(candidates)), key=lambda n: -scores[n])
    return [candidates[n] for n in order[:TOP_N]]


# STEP 8. Generate. The prompt has two halves: a PREAMBLE that is the same for every question (so it is cached)
#         and a TAIL that changes every time (the chunks that won, then the question). The preamble carries the
#         desk rules and a catalogue of the shelves, so the model can say "not in what I was given, see section X".
RULES = ("You are KAVI, the operations desk assistant at Kaveri Freight. Answer the dispatcher from the CHUNKS "
         "provided and nothing else. Cite the chunk label in square brackets after each fact. If the chunks do not "
         "contain the answer, say exactly what is missing and name the catalogue entry most likely to hold it. "
         "Never promise a release time the chunks do not state. Keep it under 150 words.")


def preamble(shelves):
    catalogue = "\n".join("- " + title_of(c) + " " + s for c, s in zip(shelves["chunks"], shelves["sentences"]))
    return RULES + "\n\nCATALOGUE OF THE SHELVES (every chunk that exists, with its context sentence):\n" + catalogue


def generate(system_text, chunks, top, question):
    tail = "CHUNKS:\n\n" + "\n\n".join(chunks[i] for i in top) + "\n\nQUESTION: " + question
    if DRY_RUN:
        system = system_text
    else:
        # cache_control marks the end of the stable prefix. The first question writes the cache; every later question
        # in the next five minutes reads it at a tenth of the price. Below 512 tokens nothing is cached (Fable's floor).
        system = [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]
    reply = create_message(model=MODEL, max_tokens=MAX_TOKENS, system=system,
                           messages=[{"role": "user", "content": tail}])
    if reply.stop_reason == "refusal":
        return "(the model declined to answer)", reply.usage
    if reply.stop_reason == "max_tokens":
        raise RuntimeError("Reply cut off at max_tokens. Raise MAX_TOKENS.")
    return text_of(reply).strip(), reply.usage


def answer(shelves, question):
    """The whole bottom lane for one question. Returns what each stage produced, so the run can be read."""
    kw = bm25_search(shelves["bm25"], question)
    vec = vector_search(shelves["vectors"], question)
    candidates = fuse([kw, vec])
    top = rerank(question, shelves["chunks"], candidates)
    text, usage = generate(preamble(shelves), shelves["chunks"], top, question)
    return {"bm25": kw, "vector": vec, "fused": candidates, "top": top, "answer": text, "usage": usage}


# ---------------------------------------------------------------

def short_labels(chunks):
    """'[SOP 214 - 4. Re-filing an e-way bill after a hold]' -> '§4. Re-filing an e-way bill after a hold'"""
    return [title_of(c).replace("[SOP 214 - ", "§").replace("]", "") for c in chunks]


def rank_of(ranked, labels, section_number):
    """1-based position of the chunk whose label starts with this section number, in a ranked list of indexes."""
    for pos, i in enumerate(ranked, 1):
        if labels[i].lstrip("§").startswith(str(section_number) + "."):
            return pos
    return "-"


if __name__ == "__main__":
    print("# E10 · two lanes · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))

    # ---- INGEST LANE, run twice: plain shelves and situated shelves. One model call, in the situated run.
    print()
    print("=== INGEST LANE (runs when the SOPs change) ===")
    plain = ingest(SOP, situated=False)
    situated = ingest(SOP, situated=True)
    labels = short_labels(plain["chunks"])
    section4 = [i for i, l in enumerate(labels) if l.startswith("§4.")][0]
    print("chunked on headings : " + str(len(plain["chunks"])) + " chunks")
    print("situated            : " + str(len(situated["sentences"])) + " context sentences written, one per chunk"
          + (" (toy, from the titles)" if DRY_RUN else " (1 model call)"))
    print("indexed             : vectors x" + str(len(situated["vectors"])) + ", BM25 vocabulary "
          + str(len(plain["bm25"]["df"])) + " words (plain) -> " + str(len(situated["bm25"]["df"])) + " words (situated)")
    print()
    print("The sentence situate wrote in front of section 4:")
    print("  " + situated["sentences"][section4])

    # ---- QUERY LANE, per question. Two model calls each: rerank, generate.
    for q in QUESTIONS:
        print()
        print("=== QUERY LANE · " + repr(q) + " ===")
        before = {"bm25": bm25_search(plain["bm25"], q), "vector": vector_search(plain["vectors"], q)}
        run = answer(situated, q)
        print("where section 4 (re-filing) ranks, plain shelves -> situated shelves:")
        print("  BM25   : #" + str(rank_of(before["bm25"], labels, 4)) + " -> #" + str(rank_of(run["bm25"], labels, 4)))
        print("  vector : #" + str(rank_of(before["vector"], labels, 4)) + " -> #" + str(rank_of(run["vector"], labels, 4)))
        print("fused candidates    : " + ", ".join(labels[i] for i in run["fused"][:5]) + " ...")
        print("reranked top-" + str(TOP_N) + "      : " + ", ".join(labels[i] for i in run["top"]))
        u = run["usage"]
        log_line({"stage": "generate", "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                  "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
                  "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0})
        print("answer:")
        print("  " + run["answer"].replace("\n", "\n  "))

    print()
    print("=== THE TWO CLOCKS ===")
    print("ingest lane : 1 situate call per ingest run. 400 SOPs, weekly: a few hundred calls a week, paid once.")
    print("query lane  : 2 calls per question (rerank, generate). 40,000 questions a day: 80,000 calls a day.")
    print("The ingest lane's cost is a rounding error on the query lane's. That is why situate is a bargain.")
    print("The cache_read figure on the second question is the preamble coming back at a tenth of the price.")
