# E2 · The bloat audit — price the belt, then trim it (objective 3.1)
import json, os
ALL9 = json.load(open("tools_all9.json", encoding="utf-8"))
CORE3 = {"get_shipment_status", "find_alternate_carriers", "process_refund"}   # what the logs say was used
core = [t for t in ALL9 if t["name"] in CORE3]

def price(tools):
    if os.getenv("DRY_RUN"):                       # free bench: ~4 chars per token
        return len(json.dumps(tools)) // 4
    import anthropic                               # live: the API's own free count_tokens
    client = anthropic.Anthropic()
    r = client.messages.count_tokens(model="claude-haiku-4-5", tools=tools,
                                     messages=[{"role": "user", "content": "hi"}])
    return r.input_tokens

daily = 40_000
nine, three = price(ALL9), price(core)
print(f"{len(ALL9)} tools: {nine} tokens / call")
print(f"{len(core)} tools: {three} tokens / call")
print(f"belt tax: {(nine - three) * daily:,} tokens/day for tools the logs say were called 0 times last week")
