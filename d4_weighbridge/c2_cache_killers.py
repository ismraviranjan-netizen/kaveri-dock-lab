# c2_cache_killers.py — five requests that look identical and are not: what silently empties the cache
# Companion to c1. The rule is a prefix match: tools -> system -> messages, byte for byte. One changed byte
# before the breakpoint and every call pays full price again. This file shows the four usual culprits,
# the repair, and the max_tokens=0 keep-alive that holds a Fable 5.1 cache warm for nearly nothing.
#
#   python c2_cache_killers.py             live on claude-fable-5-1 (pip install anthropic, ANTHROPIC_API_KEY)
#   python c2_cache_killers.py --dry       offline: predicts each receipt from the rule, no key
import json, sys, time, datetime, uuid

MODEL = "claude-fable-5-1"
PRICE = {"input": 10.00, "cache_write": 12.50, "cache_read": 0.25, "output": 50.00}
DRY = "--dry" in sys.argv

def stable_prefix():                               # same material as c1: SOP + examples + notes
    canon = open("canon.md", encoding="utf-8").read()
    sop = [json.loads(l) for l in open("sop_corpus_chunks.jsonl", encoding="utf-8")]
    return ("You are KAVI, the Kaveri dispatch-desk agent. Decide, then one sentence to the customer.\n"
            "<sop>" + "\n".join(c["text"] for c in sop) + "</sop>\n<reference>" + canon + "</reference>")

CASE = "Hold on KF-8908 at Pimpri has passed 23 hours with no confirmed reason from the officer."
FACTS = {"officer_confirmed": False, "hold_hours": 23, "depot": "Pimpri"}

# ---- five ways to send the same request. Each returns (system blocks, user content) -----------------
def v_clean(p):        # 1. frozen prefix, breakpoint on it, the varying case after it
    return [{"type": "text", "text": p, "cache_control": {"type": "ephemeral"}}], CASE

def v_timestamp(p):    # 2. a timestamp inside the cached block: changes every second
    return [{"type": "text", "text": f"Now: {datetime.datetime.now().isoformat()}\n{p}",
             "cache_control": {"type": "ephemeral"}}], CASE

def v_request_id(p):   # 3. a per-request id inside the cached block: never the same twice
    return [{"type": "text", "text": f"request {uuid.uuid4()}\n{p}", "cache_control": {"type": "ephemeral"}}], CASE

def v_unsorted(p):     # 4. facts dumped as a dict before the breakpoint: key order is not guaranteed
    facts = dict(reversed(list(FACTS.items()))) if int(time.time()) % 2 else FACTS
    return [{"type": "text", "text": p + "\n<facts>" + json.dumps(facts) + "</facts>",
             "cache_control": {"type": "ephemeral"}}], CASE

def v_repaired(p):     # 5. the fix: volatile things go AFTER the breakpoint, facts sorted
    return ([{"type": "text", "text": p, "cache_control": {"type": "ephemeral"}},
             {"type": "text", "text": f"Now: {datetime.datetime.now().isoformat()}  request {uuid.uuid4()}"}],
            "<facts>" + json.dumps(FACTS, sort_keys=True) + "</facts>\n" + CASE)

VARIANTS = [("clean", v_clean, "same bytes twice -> write, then read"),
            ("timestamp", v_timestamp, "clock inside the block -> write, write"),
            ("request_id", v_request_id, "uuid inside the block -> write, write"),
            ("unsorted dict", v_unsorted, "key order may flip -> read or write, by luck"),
            ("repaired", v_repaired, "volatile after the breakpoint -> write, then read")]

# ---- receipts --------------------------------------------------------------------------------------
def usage_row(u, max_tokens):
    w, r = getattr(u, "cache_creation_input_tokens", 0) or 0, getattr(u, "cache_read_input_tokens", 0) or 0
    cost = (u.input_tokens * PRICE["input"] + w * PRICE["cache_write"] + r * PRICE["cache_read"]
            + u.output_tokens * PRICE["output"]) / 1e6
    return {"input": u.input_tokens, "write": w, "read": r, "out": u.output_tokens, "cost": cost, "max": max_tokens}

def live(client, system, user, max_tokens=120):
    r = client.messages.create(model=MODEL, max_tokens=max_tokens, system=system,
                               messages=[{"role": "user", "content": user}])
    return usage_row(r.usage, max_tokens)

class _U:
    def __init__(self, i, w, r, o): self.input_tokens, self.cache_creation_input_tokens, self.cache_read_input_tokens, self.output_tokens = i, w, r, o

def dry(name, call_no, prefix_tokens, max_tokens=120):
    tail, out = 40, (0 if max_tokens == 0 else 50)
    hit = {"clean": call_no > 1, "timestamp": False, "request_id": False,
           "unsorted dict": call_no > 1 and call_no % 2 == 0, "repaired": call_no > 1}[name]
    return usage_row(_U(tail, 0 if hit else prefix_tokens, prefix_tokens if hit else 0, out), max_tokens)

if __name__ == "__main__":
    p = stable_prefix()
    client = None
    if not DRY:
        try:
            import anthropic
            client = anthropic.Anthropic()
        except Exception as e:
            print(f"live call unavailable ({type(e).__name__}); running --dry instead")
    prefix_tokens = len(p) // 4
    print(f"{MODEL} · prefix ≈ {prefix_tokens:,} tokens · each variant sent twice, 2 s apart")
    print(f"\n  {'variant':<14}{'call':>5}{'write':>8}{'read':>8}{'$':>9}   verdict")
    for name, fn, why in VARIANTS:
        rows = []
        for n in (1, 2):
            if client:
                system, user = fn(p); rows.append(live(client, system, user)); time.sleep(2)
            else:
                rows.append(dry(name, n, prefix_tokens))
            r = rows[-1]
            print(f"  {name:<14}{n:>5}{r['write']:>8}{r['read']:>8}{r['cost']:>9.4f}", end="")
            print(f"   {'HIT' if r['read'] else 'miss'}" if n == 2 else "")
        print(f"  {'':<14}{'':>5}{'':>8}{'':>8}{'':>9}   {why}")

    # ---- the keep-alive: refresh the clean entry for the price of a read and zero output ----------
    print("\nkeep-alive · same clean request with max_tokens=0: no answer generated, entry timer reset")
    system, user = v_clean(p)
    r = live(client, system, user, max_tokens=0) if client else dry("clean", 2, prefix_tokens, max_tokens=0)
    print(f"  {'keep-alive':<14}{'':>5}{r['write']:>8}{r['read']:>8}{r['cost']:>9.4f}   "
          f"{'cache read only, 0 output tokens' if r['read'] else 'entry had expired: this call rewrote it'}")
    print("  on Fable 5.1 a read is 0.025x input price, so one of these every 4-5 minutes beats the 1-hour TTL (2x write)")

    print("\nrule: tools -> system -> messages is one byte string. Freeze everything before the breakpoint;"
          "\n      clocks, ids, per-request facts and the question itself go after it. Verify with usage.cache_read_input_tokens.")
