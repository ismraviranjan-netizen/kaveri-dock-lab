# E7 · The agent loop — every branch explicit (objective 1.3c: the 50 percent row)
# A loop around messages.create that keeps going while the model asks for tools and stops when it doesn't.
# The field that steers it is stop_reason. BUDGET is written before the loop exists; escalation is the floor.
# D1_SCENARIO=default|truncate|refuse|exhaust (with DRY_RUN=1) makes the stand-in exercise each branch.
import json
from common import make_client, trace, text_of, fake_status, fake_carriers, MODEL_MAIN, MAX_TOKENS, TOOLS_KAVERI, DRY_RUN, SCENARIO

BUDGET = 6                                              # the retainer's cap
TOOLS = TOOLS_KAVERI                                    # the detective's toolbag: two kaveri tools

def run_tool(call):
    if call.name == "get_shipment_status":
        return fake_status(call.input["consignment_id"])
    if call.name == "find_alternate_carriers":
        return fake_carriers(call.input["lane"])
    return {"error": f"unknown tool {call.name}"}        # a structured error, not an exception: he can adapt

def escalate(brief, why):
    return f"ESCALATED to Meera's desk ({why}): {brief[:60]}"

def investigate(brief):
    msgs = [{"role": "user", "content": brief}]          # the case file; the API is stateless, so the file IS the memory
    client = make_client()
    partial = ""                                         # text that arrived before a max_tokens cut
    for turn in range(1, BUDGET + 1):                    # bounded, always; never while True
        r = client.messages.create(model=MODEL_MAIN, max_tokens=MAX_TOKENS, tools=TOOLS, messages=msgs)
        trace(turn, r)
        match r.stop_reason:
            case "tool_use":                             # the loop's fuel
                msgs.append({"role": "assistant", "content": r.content})
                results = [{"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(run_tool(b))}
                           for b in r.content if b.type == "tool_use"]
                msgs.append({"role": "user", "content": results})
            case "end_turn":                             # the natural exit
                return partial + text_of(r)
            case "max_tokens":                           # truncated, not done
                partial += text_of(r)
                msgs.append({"role": "assistant", "content": r.content})
                msgs.append({"role": "user", "content": "Continue."})
            case "pause_turn":                           # server loop paused; send it back to resume
                msgs.append({"role": "assistant", "content": r.content})
            case "refusal":                              # declined: a different path, never a blind retry
                return escalate(brief, "model refused")
            case _:                                      # stop_sequence, context exceeded, next quarter's value
                return escalate(brief, f"unhandled: {r.stop_reason}")
    return escalate(brief, "budget exhausted")          # the floor: case open, human takes it, with a reason

if __name__ == "__main__":
    print(f"# E7 · agent loop · {'DRY_RUN' if DRY_RUN else 'LIVE'} · scenario={SCENARIO} · BUDGET={BUDGET}")
    print(investigate("Why is KF-2481 stuck, and what are our options?"))
