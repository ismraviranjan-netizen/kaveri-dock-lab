# E1 · The augmented LLM — KAVI triages one exception (objective 1.3a: the cell every organism is built from)
# One call, one tool, no loop beyond a single round-trip. DRY_RUN=1 swaps in the scripted stand-in: zero paid calls.
import json
from common import make_client, trace, text_of, fake_status, MODEL_MAIN, MAX_TOKENS, EMAIL, TOOLS_KAVERI, DRY_RUN

TOOLS = [TOOLS_KAVERI[0]]                        # one phone-book entry: get_shipment_status
SYSTEM = ("You triage Kaveri shipment exceptions. Reply as JSON {category, urgency}. "
          "Categories: delay, damage, customs, refund, address, other.")

def triage(email_text):
    client = make_client()
    msgs = [{"role": "user", "content": email_text}]
    msg = client.messages.create(model=MODEL_MAIN, max_tokens=MAX_TOKENS, system=SYSTEM, tools=TOOLS, messages=msgs)
    trace(1, msg)
    if msg.stop_reason == "tool_use":            # the clerk opened a drawer
        call = next(b for b in msg.content if b.type == "tool_use")
        result = fake_status(call.input["consignment_id"])          # canned world; live, this is the MCP tool
        msgs += [{"role": "assistant", "content": msg.content},    # replay the clerk's own turn, or amnesia
                 {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call.id,
                                               "content": json.dumps(result)}]}]
        msg = client.messages.create(model=MODEL_MAIN, max_tokens=MAX_TOKENS, system=SYSTEM, tools=TOOLS, messages=msgs)
        trace(2, msg)
    return text_of(msg)

if __name__ == "__main__":
    print(f"# E1 · augmented LLM · {'DRY_RUN: scripted stand-in, 0 paid calls' if DRY_RUN else 'LIVE'}")
    print(triage(EMAIL))
