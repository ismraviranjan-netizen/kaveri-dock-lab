# E9 · One ticket, end to end — the eight hops of E1–E8 on one request (the building, not the rooms)
import asyncio, json, os, re, time, uuid
os.environ.setdefault("DRY_RUN", "1")                  # the toy foreman is enough, as in E6
from fastmcp import Client
from e1_kaveri_mcp import mcp                           # E1 · the connector (tools, resource, prompt)
from e4_chunking import by_heading, doc                 # E4 · the shelves (heading chunks)
from e5_hybrid import hybrid                            # E5 · the register + the foreman

QUESTION = "Where is KF-2481 right now, and what do I do to get it out of customs hold?"
USER, CALLER = "sunita.k", "kavi-agent"                 # two identities travel together
ALL9 = json.load(open("tools_all9.json", encoding="utf-8"))
REGISTER = []                                           # the camera's tape for this one ticket

# ── hop 1 · E7 · the door: trace id minted ONCE, before anything is answered ──
TRACE = uuid.uuid4().hex[:8]
T0 = time.perf_counter()

def log(**row):                                         # E7 · one JSON line per stage
    row = {"trace": TRACE, **row}; REGISTER.append(row); print("  ", json.dumps(row))

def ms_since(t):
    return round((time.perf_counter() - t) * 1000)

# ── hop 2 · E6 · the router: one question, two shapes ────────────────────────
def route(q):
    intents = []
    if re.search(r"KF-\d{4}", q):                                    intents.append("structured_lookup")
    if re.search(r"\bhow many\b|\bcount\b|\btotal\b", q, re.I):      intents.append("sql_aggregate")
    if re.search(r"\bwhat do i do\b|\bhow do i\b|\bsteps?\b", q, re.I): intents.append("hybrid_rag")
    return intents

# ── hop 3 · E3 · the gate: authorize → audit → tool, always in that order ─────
GRANTED  = {"kavi-agent": {"status:read", "draft:write"}}           # never refund:write
REQUIRED = {"get_shipment_status": "status:read", "process_refund": "refund:write"}

def authorize(caller, tool):
    need = REQUIRED[tool]
    if need not in GRANTED[caller]:
        raise PermissionError(f"{caller} lacks {need} for {tool}")
    return need

# ── hop 4 · E1 · the connector: a tool call and a resource read, one server ──
async def connector(cid):
    async with Client(mcp) as c:
        status = (await c.call_tool("get_shipment_status", {"consignment_id": cid})).data
        sop    = (await c.read_resource("sop://214"))[0].text
    return status, sop

# ── hop 5 · E4 + E5 · the shelves: heading chunks, hybrid search, top-k ───────
def shelves(status, k=3):
    q = f"{status['missing']} re-filing"                             # hop 4's fact sharpens hop 5's query
    return q, hybrid(q, by_heading(doc), k=k)

# ── hop 6 · E2 + E8 · the belt and the window: lean belt, cached preamble ─────
BELT = {"get_shipment_status", "find_alternate_carriers", "generate_eway_bill", "escalate_to_human"}

def window(chunks, question):
    belt      = [t for t in ALL9 if t["name"] in BELT]
    belt_tok  = len(json.dumps(belt)) // 4                           # E2's free bench
    nine_tok  = len(json.dumps(ALL9)) // 4
    chunk_tok = sum(len(c) for c in chunks) // 4
    preamble, cache_hit = 600, 0.1                                   # E8's cached fixed instructions
    q_tok     = len(question) // 4
    return dict(belt=len(belt), belt_tok=belt_tok, belt_tax_avoided=nine_tok - belt_tok,
                chunk_tok=chunk_tok, preamble_equiv=int(preamble * cache_hit),
                total_equiv=int(preamble * cache_hit) + belt_tok + chunk_tok + q_tok)

# ── hop 7 · the dials: mid-tier model, 3 s carrier timeout, honest fallback ───
DIALS = dict(model="sonnet-class", k=20, rerank=True, carrier_timeout_ms=3000)

def carrier_eta(carrier="BlueDart", takes_ms=610):
    if takes_ms > DIALS["carrier_timeout_ms"]:                       # cut it, label it stale
        return {"carrier": carrier, "eta": "as of 10:15", "stale": True}
    time.sleep(takes_ms / 1000)
    return {"carrier": carrier, "eta": "Thu 16:00", "stale": False}

def draft(status, top1, eta):
    return (f"{status['id']} is in {status['status']} (missing: {status['missing']}). "
            f"Follow {top1} Steps 1–6 to re-file. Carrier ETA {eta['eta']}"
            f"{' [stale]' if eta['stale'] else ''}. No delivery date promised.")

# ── hop 8 · E7 · the cameras: the total line, then p95 not mean ──────────────
def p95(xs):
    xs = sorted(xs); return xs[int(0.95 * len(xs)) - 1]

if __name__ == "__main__":
    print(f"# ticket {TRACE} · {USER} via {CALLER}\n# q: {QUESTION}\n")

    print("# hop 2 · E6 · router")
    t = time.perf_counter(); intents = route(QUESTION)
    log(stage="route", ms=ms_since(t), intents=intents, caller=CALLER, user=USER)

    print("# hop 3 · E3 · gate")
    t = time.perf_counter()
    try:
        need = authorize(CALLER, "get_shipment_status")
        log(stage="authz", ms=ms_since(t), tool="get_shipment_status", needed=need, decision="ALLOW")
    except PermissionError as e:
        log(stage="authz", ms=ms_since(t), tool="get_shipment_status", decision="DENY", reason=str(e)); raise

    print("# hop 4 · E1 · connector")
    t = time.perf_counter(); status, sop = asyncio.run(connector("KF-2481"))
    log(stage="tool", ms=ms_since(t), tool="mcp__kaveri__get_shipment_status", result=status["status"])
    log(stage="resource", ms=0, uri="sop://214", chars=len(sop), note="read into context, no tool call")

    print("# hop 5 · E4+E5 · shelves")
    t = time.perf_counter(); rag_q, top = shelves(status)
    log(stage="retrieve", ms=ms_since(t), query=rag_q, k=len(top), top1=top[0])

    print("# hop 6 · E2+E8 · belt + window")
    t = time.perf_counter(); w = window(by_heading(doc)[:3], QUESTION)
    log(stage="assemble", ms=ms_since(t), **w)

    print("# hop 7 · dials + draft")
    t = time.perf_counter(); eta = carrier_eta()
    log(stage="carrier_eta", ms=ms_since(t), **eta, timeout_ms=DIALS["carrier_timeout_ms"])
    t = time.perf_counter(); answer = draft(status, top[0], eta)
    log(stage="draft", ms=ms_since(t), model=DIALS["model"], rerank=DIALS["rerank"])

    print("# hop 8 · E7 · cameras")
    log(stage="total", ms=ms_since(T0), cites=[top[0]], promised_date=False)

    print(f"\n# answer -> {answer}")
    print(f"# register: {len(REGISTER)} lines, one trace id · stage p95 would read {p95([r['ms'] for r in REGISTER[:-1]])} ms")
