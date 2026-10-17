# E9 · One ticket, end to end: the eight hops of E1 to E8 on one request  (the building, not the rooms)
#
#   hop 1  E7  the door: trace id minted once
#   hop 2  E6  the router: one question, two shapes
#   hop 3  E3  the gate: authorize -> audit -> tool
#   hop 4  E1  the connector: a tool call and a resource read through MCP
#   hop 5  E4 + E5  the shelves: heading chunks, hybrid search, top-k
#   hop 6  E2 + E8  the belt and the window: lean belt, cached preamble, priced
#   hop 7  the dials and the draft: carrier timeout, a real model call, its usage on the register
#   hop 8  E7  the cameras: the total line
#
# Needs:  pip install fastmcp   (hop 4 goes through E1's server)
# Run on battery:  DRY_RUN=1 python e9_one_ticket.py        Run live:  python e9_one_ticket.py

import asyncio
import json
import re
import time
import uuid
from common import ask_usage, count_tokens, paise, belt, ALL9, SOP, MODEL, DRY_RUN
from e1_connector import mcp, Client                      # E1 · the connector (tools, resource, prompt)
from e3_gate_pass import authorize, audit_log             # E3 · the gate
from e4_chunking import by_heading                        # E4 · the shelves
from e5_hybrid import hybrid                              # E5 · the register + the foreman


# ---------------------------------------------------------------
# STEP 0. The ticket, the two identities, and the dials
# ---------------------------------------------------------------

QUESTION = "Where is KF-2481 right now, and what do I do to get it out of customs hold?"
USER, CALLER = "sunita.k", "kavi-agent"                   # the person and the service account travel together
CHUNKS = by_heading(SOP)
BELT = {"get_shipment_status", "find_alternate_carriers", "generate_eway_bill", "escalate_to_human"}
DIALS = {"model": MODEL, "k": 3, "rerank": True, "carrier_timeout_ms": 3000}
REGISTER = []                                             # the camera's tape for this one ticket


# ---------------------------------------------------------------
# hop 1 · E7 · the door: the trace id is minted ONCE, before anything is answered
# ---------------------------------------------------------------

TRACE = uuid.uuid4().hex[:8]
T0 = time.perf_counter()


def log(**row):
    row = {"trace": TRACE, **row}
    REGISTER.append(row)
    print("  " + json.dumps(row))


def ms_since(start):
    return round((time.perf_counter() - start) * 1000)


# ---------------------------------------------------------------
# hop 2 · E6 · the router: one question can carry two shapes
# ---------------------------------------------------------------

def route(question):
    intents = []
    if re.search(r"KF-\d{4}", question):
        intents.append("structured_lookup")
    if re.search(r"\bhow many\b|\bcount\b|\btotal\b", question, re.I):
        intents.append("sql_aggregate")
    if re.search(r"\bwhat do i do\b|\bhow do i\b|\bsteps?\b", question, re.I):
        intents.append("hybrid_rag")
    return intents


# ---------------------------------------------------------------
# hop 4 · E1 · the connector: a tool call and a resource read, one server
# ---------------------------------------------------------------

async def connector(consignment_id):
    async with Client(mcp) as server:
        status = (await server.call_tool("get_shipment_status", {"consignment_id": consignment_id})).data
        sop = (await server.read_resource("sop://214"))[0].text
    return status, sop


# ---------------------------------------------------------------
# hop 6 · E2 + E8 · the belt and the window, priced
# ---------------------------------------------------------------

def window(chunks, question):
    lean = belt(BELT)
    belt_tok = count_tokens(tools=lean)
    nine_tok = count_tokens(tools=ALL9)
    chunk_tok = count_tokens(text="\n\n".join(chunks))
    preamble, cache_hit = 600, 0.1                        # E8's cached fixed instructions
    return {"belt": len(lean), "belt_tok": belt_tok, "belt_tax_avoided": nine_tok - belt_tok,
            "chunk_tok": chunk_tok, "preamble_equiv": int(preamble * cache_hit),
            "total_equiv": int(preamble * cache_hit) + belt_tok + chunk_tok + count_tokens(text=question)}


# ---------------------------------------------------------------
# hop 7 · the dials: a carrier timeout with an honest fallback, then the draft
# ---------------------------------------------------------------

def carrier_eta(carrier="BlueDart", takes_ms=610):
    if takes_ms > DIALS["carrier_timeout_ms"]:            # cut it, label it stale
        return {"carrier": carrier, "eta": "as of 10:15", "stale": True}
    time.sleep(takes_ms / 1000)
    return {"carrier": carrier, "eta": "Thu 16:00", "stale": False}


def draft(status, section, eta):
    prompt = ("Draft the dispatcher's answer in under 80 words, using only this SOP section and these facts. "
              "Never promise a release time.\n\nQuestion: " + QUESTION
              + "\n\nFacts: " + json.dumps(status) + "\nCarrier ETA: " + json.dumps(eta) + "\n\n" + section)
    text, tokens_in, tokens_out = ask_usage(DIALS["model"], prompt)
    return text, tokens_in, tokens_out


def p95(xs):
    xs = sorted(xs)
    return xs[int(0.95 * len(xs)) - 1]


if __name__ == "__main__":
    print("# E9 · one ticket · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))
    print("# ticket " + TRACE + " · " + USER + " via " + CALLER)
    print("# q: " + QUESTION)
    print()

    print("# hop 2 · E6 · router")
    t = time.perf_counter(); intents = route(QUESTION)
    log(stage="route", ms=ms_since(t), intents=intents, caller=CALLER, user=USER)

    print("# hop 3 · E3 · gate")
    t = time.perf_counter()
    try:
        authorize(CALLER, "get_shipment_status")
        audit_log(CALLER, "get_shipment_status", "ALLOW")
        log(stage="authz", ms=ms_since(t), tool="get_shipment_status", decision="ALLOW")
    except PermissionError as error:
        audit_log(CALLER, "get_shipment_status", "DENY", str(error))
        log(stage="authz", ms=ms_since(t), tool="get_shipment_status", decision="DENY", reason=str(error))
        raise

    print("# hop 4 · E1 · connector")
    t = time.perf_counter(); status, sop = asyncio.run(connector("KF-2481"))
    log(stage="tool", ms=ms_since(t), tool="mcp__kaveri__get_shipment_status", result=status["status"])
    log(stage="resource", ms=0, uri="sop://214", chars=len(sop), note="read into context, no tool call")

    print("# hop 5 · E4+E5 · shelves")
    t = time.perf_counter()
    rag_q = status["missing"] + " re-filing"              # hop 4's fact sharpens hop 5's query
    top = hybrid(rag_q, CHUNKS, k=DIALS["k"])
    section = [c for c in CHUNKS if c.startswith(top[0])][0]
    log(stage="retrieve", ms=ms_since(t), query=rag_q, k=len(top), top1=top[0])

    print("# hop 6 · E2+E8 · belt + window")
    t = time.perf_counter(); w = window([section], QUESTION)
    log(stage="assemble", ms=ms_since(t), **w)

    print("# hop 7 · dials + draft")
    t = time.perf_counter(); eta = carrier_eta()
    log(stage="carrier_eta", ms=ms_since(t), **eta, timeout_ms=DIALS["carrier_timeout_ms"])
    t = time.perf_counter(); answer, tokens_in, tokens_out = draft(status, section, eta)
    log(stage="draft", ms=ms_since(t), model=DIALS["model"], tokens_in=tokens_in, tokens_out=tokens_out,
        cost_pc=paise(DIALS["model"], tokens_in, tokens_out), rerank=DIALS["rerank"])

    print("# hop 8 · E7 · cameras")
    log(stage="total", ms=ms_since(T0), cites=[top[0]], promised_date=False)

    print()
    print("# answer -> " + answer)
    print("# register: " + str(len(REGISTER)) + " lines, one trace id · stage p95 would read "
          + str(p95([r["ms"] for r in REGISTER[:-1]])) + " ms")
