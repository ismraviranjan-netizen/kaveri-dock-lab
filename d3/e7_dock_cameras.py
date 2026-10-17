# E7 · The dock cameras: one real ticket through the register, then the canned day's gauges  (objective 3.4, Law 4)
#
#   Logs:    one JSON line per stage. WHAT happened.
#   Traces:  one id minted at the door, stamped on every line. WHERE did this ticket lose time.
#   Metrics: computed FROM the register: mean and p95 per stage. IS today normal. SLAs live in the p95.
#   The draft stage is a real model call, and its usage block is what the camera records: tokens and paise.
#
# Run on battery:  DRY_RUN=1 python e7_dock_cameras.py      Run live:  python e7_dock_cameras.py

import json
import re
import time
import uuid
from collections import defaultdict
from common import ask_usage, paise, MODEL, SOP, LOGDAY, DRY_RUN
from e4_chunking import by_heading
from e5_hybrid import bm25ish, title_of

CHUNKS = by_heading(SOP)


# ---------------------------------------------------------------
# STEP 0. The register: one JSON line per event. print() stands in for the log shipper.
# ---------------------------------------------------------------

def log(**row):
    print("  " + json.dumps(row))


def ms_since(start):
    return round((time.perf_counter() - start) * 1000)


# ---------------------------------------------------------------
# STEP 1. The three stages of one ticket. Each returns (result, tokens, paise).
# ---------------------------------------------------------------

def route_it(question):
    return ("hybrid_rag" if not re.search(r"KF-\d{4}", question) else "structured_lookup"), 0, 0


def fetch_chunks(question, k=1):
    scores = bm25ish(question, CHUNKS)                       # the register only: no model, no bill
    order = sorted(range(len(CHUNKS)), key=lambda i: -scores[i])
    return [CHUNKS[i] for i in order[:k]], 0, 0


def draft_reply(question, chunks):
    prompt = ("Draft the dispatcher's answer in under 80 words, using only this SOP section. "
              "Never promise a release time.\n\nQuestion: " + question + "\n\n" + chunks[0])
    text, tokens_in, tokens_out = ask_usage(MODEL, prompt)
    return text, tokens_in + tokens_out, paise(MODEL, tokens_in, tokens_out)


# ---------------------------------------------------------------
# STEP 2. One ticket: the trace id is minted ONCE, outside the stage loop.
#         Sabotage: mint it inside the loop. digest() still works. The journey is gone.
# ---------------------------------------------------------------

def one_ticket(question):
    trace = uuid.uuid4().hex[:8]
    t0 = time.perf_counter()

    s = time.perf_counter(); road, tok, pc = route_it(question)
    log(trace=trace, stage="route", ms=ms_since(s), tokens=tok, cost_pc=pc, road=road)

    s = time.perf_counter(); chunks, tok, pc = fetch_chunks(question)
    log(trace=trace, stage="retrieve", ms=ms_since(s), tokens=tok, cost_pc=pc, top1=title_of(chunks[0]))

    s = time.perf_counter(); answer, tok, pc = draft_reply(question, chunks)
    log(trace=trace, stage="draft", ms=ms_since(s), tokens=tok, cost_pc=pc, model=MODEL)

    log(trace=trace, stage="total", ms=ms_since(t0))
    return answer


# ---------------------------------------------------------------
# STEP 3. The gauges, computed from the register. p95, not mean.
# ---------------------------------------------------------------

def p95(xs):
    xs = sorted(xs)
    return xs[int(0.95 * len(xs)) - 1]


def digest(path=LOGDAY):
    series = defaultdict(list)
    for line in open(path):
        row = json.loads(line)
        series[row["stage"]].append(row["ms"])
    for stage in ("route", "retrieve", "draft", "total"):
        xs = series[stage]
        mean = sum(xs) / len(xs)
        p = p95(xs)
        flag = "  <- the mean lied" if p > 4 * mean else ""
        print("  " + stage.ljust(9) + "mean=" + format(mean, ",.0f").rjust(7) + "ms  p95=" + format(p, ",").rjust(6) + "ms" + flag)


if __name__ == "__main__":
    print("# E7 · dock cameras · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))

    print("=== One ticket through the cameras ===")
    print(one_ticket("How do I re-file an e-way bill after a hold?"))

    print()
    print("=== The canned day, digested (10,000 tickets) ===")
    if not LOGDAY.exists():
        from gen_logday import write
        print("  (data/logday.jsonl missing: writing it now, " + format(write(), ",") + " lines)")
    digest()
