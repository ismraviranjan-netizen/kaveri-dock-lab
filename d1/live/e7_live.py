# e7_live.py
# E7: the agent loop. A loop around messages.create that keeps going while the model asks for tools
# and stops when it does not. The field that steers it is stop_reason. EVERY value lands somewhere explicit.
#   BUDGET is written before the loop exists. Escalation to a human is the floor.
#
# Before running:   pip install anthropic   and   ANTHROPIC_API_KEY in the environment
# Run:              python e7_live.py

import json
import anthropic


# ---------------------------------------------------------------
# STEP 0. Things we decide before the loop exists
# ---------------------------------------------------------------

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 1024
BUDGET = 6                        # the most turns we will ever pay for. Never "while True".

BRIEF = "Why is consignment KF-2481 stuck, and what are our options? Use the tools, then give a short recommendation."

# Two tools the detective may ask for. Descriptions only; we run them.
TOOLS = [
    {
        "name": "get_shipment_status",
        "description": "Live status for one Kaveri consignment id (e.g. KF-2481).",
        "input_schema": {
            "type": "object",
            "properties": {"consignment_id": {"type": "string"}},
            "required": ["consignment_id"],
        },
    },
    {
        "name": "find_alternate_carriers",
        "description": "Carriers that can take a lane (e.g. Pune-Chennai) within 48 hours.",
        "input_schema": {
            "type": "object",
            "properties": {"lane": {"type": "string"}},
            "required": ["lane"],
        },
    },
]


# ---------------------------------------------------------------
# STEP 1. The tools themselves. Plain Python. Swap for real lookups in production.
# ---------------------------------------------------------------

def get_shipment_status(consignment_id):
    return {"id": consignment_id, "status": "CUSTOMS_HOLD", "missing": "e-way bill", "days_late": 3}

def find_alternate_carriers(lane):
    return ["BlueDart", "Delhivery"]

def run_tool(tool_request):
    # Return a structured error for an unknown tool, not an exception. The model can read it and adapt.
    if tool_request.name == "get_shipment_status":
        return get_shipment_status(tool_request.input["consignment_id"])
    if tool_request.name == "find_alternate_carriers":
        return find_alternate_carriers(tool_request.input["lane"])
    return {"error": "unknown tool " + tool_request.name}


# ---------------------------------------------------------------
# STEP 2. The floor. When the loop cannot finish, a human gets the case WITH a reason.
# ---------------------------------------------------------------

def escalate(reason):
    return "ESCALATED to Meera's desk (" + reason + "): " + BRIEF


# ---------------------------------------------------------------
# STEP 3. Connect.
# ---------------------------------------------------------------

client = anthropic.Anthropic()


# ---------------------------------------------------------------
# STEP 4. The loop.
# ---------------------------------------------------------------

def investigate():
    conversation = [{"role": "user", "content": BRIEF}]     # the case file. The API is stateless, so this IS the memory.
    text_so_far = ""                                        # text that arrived before a max_tokens cut

    for turn in range(1, BUDGET + 1):                       # bounded, always

        reply = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=TOOLS,
            messages=conversation,
        )

        # One line per turn so you can watch the loop breathe.
        tool_names = []
        for block in reply.content:
            if block.type == "tool_use":
                tool_names.append(block.name)
        print("Turn", turn, "stop_reason =", reply.stop_reason, tool_names if tool_names else "")

        # Collect any text in this reply.
        text_this_turn = ""
        for block in reply.content:
            if block.type == "text":
                text_this_turn = text_this_turn + block.text

        # ---- Every stop_reason value gets its own branch. No "else" that swallows. ----

        if reply.stop_reason == "tool_use":
            # The loop's fuel. Run every tool the model asked for, send all results back.
            conversation.append({"role": "assistant", "content": reply.content})
            results = []
            for block in reply.content:
                if block.type == "tool_use":
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(run_tool(block)),
                    })
            conversation.append({"role": "user", "content": results})
            continue

        if reply.stop_reason == "end_turn":
            # The natural exit. Return everything, including any text saved from a max_tokens cut.
            return text_so_far + text_this_turn

        if reply.stop_reason == "max_tokens":
            # Truncated is not done. Keep the partial text, ask the model to continue.
            text_so_far = text_so_far + text_this_turn
            conversation.append({"role": "assistant", "content": reply.content})
            conversation.append({"role": "user", "content": "Continue."})
            continue

        if reply.stop_reason == "pause_turn":
            # A server-side tool paused the turn. Send the reply back as-is to resume.
            conversation.append({"role": "assistant", "content": reply.content})
            continue

        if reply.stop_reason == "refusal":
            # The model declined. A different path, never a blind retry.
            return escalate("model refused")

        # Anything else: stop_sequence, context window exceeded, a value that does not exist yet.
        return escalate("unhandled stop_reason " + str(reply.stop_reason))

    # The for loop ran out. The case is still open. A human takes it, with the reason.
    return escalate("budget of " + str(BUDGET) + " turns exhausted")


# ---------------------------------------------------------------
# STEP 5. Run it.
# ---------------------------------------------------------------

print("=== Agent loop, BUDGET =", BUDGET, "===")
print()
print(investigate())
