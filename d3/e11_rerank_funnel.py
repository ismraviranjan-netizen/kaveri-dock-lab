# E11 · The funnel: retrieve ~100 candidates, rerank, pass top-20, answer from those  (objective 3.6 · Law 3)
#
#   The reranking shape from Part 5: "retrieve ~150 -> rerank -> top-20, and 20 beat 5 and 10 outright."
#   E5 and E10 had ten chunks, so there was nothing to funnel. This file grows the shelf first.
#
#   INGEST (once)   SOP 214 (10 chunks) + a dozen DECOY SOPs on other desk topics, two of them LOOKALIKES about
#                   e-way bills, written by one model call the first time and saved to data/sop_decoys.md.
#                   About 100 chunks across 13 SOPs. Indexed with E10's BM25 and vector shelves.
#   QUERY (per q)   search both -> fuse -> the top CANDIDATES (100) -> ONE rerank call reads every candidate's text
#                   against the question and scores it -> top-20 -> generate from those 20.
#
#   The line to watch is "where SOP 214 §4 sits": its rank after BM25, after vector, after fusion, after rerank.
#   The lookalike SOP (e-way bill GENERATION, not re-filing) shares most of §4's words, so the cheap stages rank it
#   high. Only the reranker, which reads text against the question, can tell generation from re-filing.
#
#   Live calls: first run 1 (decoys) + 2 per question (rerank, generate). Later runs 2 per question.
# Run on battery:  DRY_RUN=1 python e11_rerank_funnel.py    Run live:  python e11_rerank_funnel.py

import re
from common import create_message, ask, ask_json, count_tokens, text_of, log_line, MODEL, MAX_TOKENS, SOP, DATA, DRY_RUN
from e4_chunking import by_heading
from e10_two_lanes import build_bm25, bm25_search, build_vectors, vector_search, fuse, RULES

CANDIDATES = 100                          # the book says ~150. The shelf here holds about 100, so: all of it.
TOP_N = 20                                # what the reranker passes on. 20 beat 5 and 10 in Anthropic's tests.
DECOYS = DATA / "sop_decoys.md"           # written once, live. Delete it to regenerate.
QUESTIONS = ("how do I re-file an e-way bill after a customs hold?",
             "parcel stuck, paperwork problem, what should I do")

DECOY_TOPICS = [
    ("SOP 231", "Generating an e-way bill for a new consignment"),          # LOOKALIKE: same words, different job
    ("SOP 232", "E-way bill validity extension for long-haul trips"),        # LOOKALIKE: extension without any hold
    ("SOP 118", "Vehicle breakdown on the road"),
    ("SOP 142", "Damaged goods claims at delivery"),
    ("SOP 155", "Cash-on-delivery reconciliation"),
    ("SOP 167", "Address correction before dispatch"),
    ("SOP 173", "Cold-chain temperature excursions"),
    ("SOP 188", "Returns pickup and reverse logistics"),
    ("SOP 190", "Driver onboarding and document checks"),
    ("SOP 205", "Weighbridge calibration and disputes"),
    ("SOP 250", "Fuel card use and reconciliation"),
    ("SOP 262", "Warehouse fire drill and evacuation"),
]


# ===============================================================
# INGEST. Grow the shelf once, then index it.
# ===============================================================

def write_decoys():
    """One model call writes twelve short SOPs in a strict markdown shape. Saved to disk: paid once, like situate."""
    if DRY_RUN:
        docs = []
        for code, title in DECOY_TOPICS:
            secs = "\n".join("## " + str(n) + ". Step group " + str(n) + "\n" + title + ": the desk checks the record, "
                             "confirms the details with the depot, records the action in the TMS and informs the customer. "
                             "Escalate to the operations lead if the case is not closed within the shift." for n in range(1, 9))
            docs.append("# " + code + " — " + title + "\n" + secs)
        return "\n\n".join(docs)
    wanted = "\n".join("- " + code + " — " + title for code, title in DECOY_TOPICS)
    prompt = ("Write twelve short standard operating procedures for Kaveri Freight & Fulfilment, Pune, one per line below. "
              "Each SOP must start with a line '# <code> — <title>' exactly as given, followed by exactly 8 sections, each "
              "starting with '## <n>. <section title>' and holding one paragraph of 50 to 80 words of concrete procedure "
              "(who does what, in the TMS, with the depot, with the customer). Use the real vocabulary of Indian road freight. "
              "SOP 231 and SOP 232 must talk about e-way bills, invoices, validity and the portal, but must NOT mention customs "
              "holds or re-filing after a hold. Output only the markdown, no preamble, no code fence.\n\n" + wanted)
    text = ask(MODEL, prompt)
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:-1])
    return text


def chunk_decoys(markdown):
    """'# SOP 231 — title' starts a document; '## n. title' starts a chunk. The label carries the SOP code."""
    chunks = []
    for doc in re.split(r"(?m)^(?=# )", markdown):
        doc = doc.strip()
        if not doc.startswith("# "):
            continue
        code = doc.splitlines()[0].lstrip("# ").split("—")[0].split("-")[0].strip()
        for part in re.split(r"(?m)^(?=## )", doc)[1:]:
            title = part.splitlines()[0].lstrip("# ").strip()
            chunks.append("[" + code + " - " + title + "]\n" + part.strip())
    return chunks


def ingest():
    if not DECOYS.exists():
        print("  (data/sop_decoys.md missing: writing it now" + ("" if DRY_RUN else ", 1 model call") + ")")
        DECOYS.write_text(write_decoys(), encoding="utf-8")
    chunks = by_heading(SOP) + chunk_decoys(DECOYS.read_text(encoding="utf-8"))
    return {"chunks": chunks, "bm25": build_bm25(chunks), "vectors": build_vectors(chunks)}


# ===============================================================
# QUERY. The funnel.
# ===============================================================

def rerank(question, chunks, candidates):
    """ONE call. Every candidate's TEXT is read against the question and scored 0..10. The top TOP_N go on."""
    if DRY_RUN:
        return candidates[:TOP_N]
    listing = "\n\n".join("CANDIDATE " + str(n) + ":\n" + chunks[i] for n, i in enumerate(candidates, 1))
    prompt = ("You are a reranker. Score each candidate 0 (useless) to 10 (answers it exactly) for THIS question. Judge by "
              "the chunk text, not the SOP title. A chunk about a similar topic that does not answer the question scores "
              "low. Reply with JSON only: a list of exactly " + str(len(candidates)) + " numbers in candidate order.\n\n"
              "Question: " + question + "\n\n" + listing)
    scores = [float(s) for s in ask_json(MODEL, prompt)]
    if len(scores) != len(candidates):
        raise RuntimeError("Reranker returned " + str(len(scores)) + " scores for " + str(len(candidates)) + " candidates.")
    order = sorted(range(len(candidates)), key=lambda n: -scores[n])
    return [candidates[n] for n in order[:TOP_N]]


def preamble(chunks):
    """Stable for every question, so it is cached: the rules plus a catalogue of every label on the shelf. Over the
    512-token cache floor, which a rules-only preamble would not be."""
    catalogue = "\n".join("- " + label(c) for c in chunks)
    return (RULES + " The chunks you receive are the top-" + str(TOP_N) + " after reranking; most will be irrelevant. "
            "Use only the ones that answer the question and cite each by its label.\n\nCATALOGUE OF THE SHELF ("
            + str(len(chunks)) + " chunks):\n" + catalogue)


def generate(system_text, chunks, top, question):
    tail = ("Draft the dispatcher's answer from these chunks.\n\nCHUNKS:\n\n" + "\n\n".join(chunks[i] for i in top)
            + "\n\nQUESTION: " + question)
    system = system_text if DRY_RUN else [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]
    reply = create_message(model=MODEL, max_tokens=MAX_TOKENS, system=system, messages=[{"role": "user", "content": tail}])
    if reply.stop_reason == "refusal":
        return "(the model declined to answer)", reply.usage
    return text_of(reply).strip(), reply.usage


# ---------------------------------------------------------------

def label(chunk):
    return chunk.splitlines()[0].strip("[]")                 # "SOP 214 - 4. Re-filing an e-way bill after a hold"


def rank_of(ranked, target):
    return ranked.index(target) + 1 if target in ranked else "-"


def sop_of(chunk):
    return label(chunk).split(" - ")[0]


if __name__ == "__main__":
    print("# E11 · rerank funnel · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))
    print()
    print("=== INGEST · grow the shelf ===")
    shelf = ingest()
    chunks = shelf["chunks"]
    sops = sorted(set(sop_of(c) for c in chunks))
    target = [i for i, c in enumerate(chunks) if label(c).startswith("SOP 214 - 4.")][0]
    print("shelf: " + str(len(chunks)) + " chunks across " + str(len(sops)) + " SOPs · the answer lives in [" + label(chunks[target]) + "]")

    for q in QUESTIONS:
        print()
        print("=== FUNNEL · " + repr(q) + " ===")
        kw = bm25_search(shelf["bm25"], q)
        vec = vector_search(shelf["vectors"], q)
        fused = fuse([kw, vec])[:CANDIDATES]
        top = rerank(q, chunks, fused)

        def mix(ranked, n):
            return str(sum(1 for i in ranked[:n] if sop_of(chunks[i]) == "SOP 214")) + " of " + str(n) + " from SOP 214"

        print("stage          where SOP 214 §4 sits   what else is near the top")
        print("BM25           #" + str(rank_of(kw, target)).ljust(22) + mix(kw, 20) + " in the top-20 · #1 is [" + label(chunks[kw[0]]) + "]")
        print("vector         #" + str(rank_of(vec, target)).ljust(22) + mix(vec, 20) + " in the top-20 · #1 is [" + label(chunks[vec[0]]) + "]")
        print("fused " + str(len(fused)).rjust(3) + "      #" + str(rank_of(fused, target)).ljust(22) + mix(fused, 20) + " in the top-20 · #1 is [" + label(chunks[fused[0]]) + "]")
        print("reranked top-" + str(TOP_N) + " #" + str(rank_of(top, target)).ljust(22) + mix(top, TOP_N) + " · #1 is [" + label(chunks[top[0]]) + "]")
        print()
        print("the reranked top-" + str(TOP_N) + ", in order:")
        for n, i in enumerate(top, 1):
            moved = rank_of(fused, i)
            print("  " + str(n).rjust(2) + ". [" + label(chunks[i]) + "]" + ("" if moved == n else "   (was #" + str(moved) + " after fusion)"))
        print()
        text, u = generate(preamble(chunks), chunks, top, q)
        cited = sorted(set(re.findall(r"\[(SOP \d+ - [^\]]+)\]", text)))
        log_line({"stage": "generate", "context_chunks": TOP_N, "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                  "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0, "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0})
        print("answer cites " + str(len(cited)) + " of the " + str(TOP_N) + " chunks: " + "; ".join(cited))
        print("answer:")
        print("  " + text.replace("\n", "\n  "))

    # The bill of the funnel, counted for free: what top-5, top-10 and top-20 cost in context tokens.
    print()
    print("=== THE BILL OF TOP-K · count_tokens, free ===")
    for k in (5, 10, 20):
        tokens = count_tokens(text="\n\n".join(chunks[i] for i in top[:k]))
        print("top-" + str(k).ljust(3) + " = " + format(tokens, ",").rjust(6) + " context tokens per question")
    print("20 beat 5 and 10 on answer quality in Anthropic's tests. The reranker is what makes the 20 worth reading:")
    print("without it, the 20 would be the fused list, and the lookalike SOPs would be in it.")
