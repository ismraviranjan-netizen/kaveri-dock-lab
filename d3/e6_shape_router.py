# E6 · The retrieval router: three shapes of question, three machines  (objective 3.6, Law 3)
#
#   An id in the question      -> structured lookup. The TMS already answers EXACTLY. No index, no model.
#   "how many", "count"        -> SQL aggregate. The database counts. A model would invent a fluent wrong number.
#   procedure prose            -> hybrid RAG: E5 finds the section, the model drafts from it.
#   The CODE routes by regex. Rule ORDER matters. Only the third road costs a model call.
#
# Run on battery:  DRY_RUN=1 python e6_shape_router.py      Run live:  python e6_shape_router.py

import re
from common import ask, MODEL, SOP, DRY_RUN
from e4_chunking import by_heading
from e5_hybrid import hybrid

CHUNKS = by_heading(SOP)


# ---------------------------------------------------------------
# STEP 0. Stubs for the two systems that already hold exact answers
# ---------------------------------------------------------------

TMS = {"KF-2481": {"status": "CUSTOMS_HOLD", "leg": "ICD Pune"}}      # the transport management system
LATE_THIS_WEEK = 41                                                     # SELECT count(*) ... WHERE late


# ---------------------------------------------------------------
# STEP 1. Three handlers, one per shape
# ---------------------------------------------------------------

def structured_lookup(question):
    consignment_id = re.search(r"KF-\d{4}", question).group()
    return TMS[consignment_id]                                          # THE row, not a guess


def sql_aggregate(question):
    return LATE_THIS_WEEK                                               # a number somebody counted


def hybrid_rag(question):
    top = hybrid(question, CHUNKS, k=1)[0]                              # E5 picks the section
    for chunk in CHUNKS:
        if chunk.startswith(top):
            section = chunk
    prompt = ("Draft the dispatcher's answer in under 80 words, using only this SOP section. "
              "Never promise a release time.\n\nQuestion: " + question + "\n\n" + section)
    return "from " + top + ": " + ask(MODEL, prompt)


# ---------------------------------------------------------------
# STEP 2. The rule table. First match wins, so order is a decision.
# ---------------------------------------------------------------

RULES = [
    (re.compile(r"\bhow many\b|\bcount\b|\btotal\b", re.I), sql_aggregate),      # aggregate language first
    (re.compile(r"KF-\d{4}"),                              structured_lookup),  # then an id
    (re.compile(r".*"),                                    hybrid_rag),         # everything else: the shelves
]


def route(question):
    for pattern, handler in RULES:
        if pattern.search(question):
            return handler.__name__, handler(question)


if __name__ == "__main__":
    print("# E6 · retrieval router · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))

    # STEP 3. Four questions, four routes. Only the last two cost a model call.
    for q in ("Where is KF-2481 right now?",
              "How many shipments ran late this week?",
              "How many times has KF-2481 been delayed?",
              "How do I re-file an e-way bill after a hold?"):
        name, answer = route(q)
        print()
        print(name.ljust(17) + " <- " + q)
        print(" " * 17 + " -> " + str(answer))
