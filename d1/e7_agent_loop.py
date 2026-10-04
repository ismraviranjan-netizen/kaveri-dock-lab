# E7 · The agent loop: every stop_reason lands somewhere explicit  (objective 1.3c, the 50 percent row)
#
# A loop around messages.create that keeps going while the model asks for tools and stops when it does not.
# The field that steers it is stop_reason. BUDGET is written before the loop exists. Escalation is the floor.
#
# Run on battery:  DRY_RUN=1 python e7_agent_loop.py
#                  D1_SCENARIO=default|truncate|refuse|exhaust makes the stand-in exercise each branch
# Run live:        python e7_agent_loop.py

import json
from common import make_client, trace, text_of, fake_status, fake_carriers, MODEL_MAIN, MAX_TOKENS, TOOLS_KAVERI, DRY_RUN, SCENARIO


# ---------------------------------------------------------------
# STEP 0. Things we decide BEFORE the loop exists
# ---------------------------------------------------------------

BUDGET = 6                                # the most turns we will ever pay for. Never "while True".
TOOLS = TOOLS_KAVERI                      # the detective's toolbag: both kaveri tools
BRIEF_E7 = "Why is KF-2481 stuck, and what are our options?"


# ---------------------------------------------------------------
# STEP 1. The tools, dispatched by name. Plain Python.
#         An unknown tool returns a structured error, not an exception: the model can read it and adapt.
# ---------------------------------------------------------------

def run_tool(tool_request):
    if tool_request.name == "get_shipment_status":
        return fake_status(tool_request.input["consignment_id"])
    if tool_request.name == "find_alternate_carriers":
        return fake_carriers(tool_request.input["lane"])
    return {"error": "unknown tool " + tool_request.name}


# ---------------------------------------------------------------
# STEP 2. The floor. When the loop cannot finish, a human gets the case WITH a reason.
# ---------------------------------------------------------------

def escalate(reason):
    return "ESCALATED to Meera's desk (" + reason + "): " + BRIEF_E7


# ---------------------------------------------------------------
# STEP 3. The loop
# ---------------------------------------------------------------

def investigate():
    client = make_client()
    conversation = [{"role": "user", "content": BRIEF_E7}]  # the case file. The API is stateless, so this IS the memory.
    text_so_far = ""                                          # text that arrived before a max_tokens cut

    for turn in range(1, BUDGET + 1):                         # bounded, always

        reply = client.messages.create(
            model=MODEL_MAIN,
            max_tokens=MAX_TOKENS,
            tools=TOOLS,
            messages=conversation,
        )
        trace(turn, reply)                                    # one line per turn, so you can watch the loop breathe

        # Collect any text in this reply.
        text_this_turn = ""
        for block in reply.content:
            if block.type == "text":
                text_this_turn = text_this_turn + block.text

        # ---- Every stop_reason value gets its own branch. No "else" that swallows. ----

        if reply.stop_reason == "tool_use":
            # The loop's fuel. Run every tool the model asked for, send all the results back.
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
            # The natural exit. Return everything, including text saved from an earlier max_tokens cut.
            return text_so_far + text_this_turn

        if reply.stop_reason == "max_tokens":
            # Truncated is not done. Keep the partial text, ask the model to continue.
            text_so_far = text_so_far + text_this_turn
            conversation.append({"role": "assistant", "content": reply.content})
            conversation.append({"role": "user", "content": "Continue."})
            continue

        if reply.stop_reason == "pause_turn":
            # A server-side tool paused the turn. Send the reply back as it is to resume.
            conversation.append({"role": "assistant", "content": reply.content})
            continue

        if reply.stop_reason == "refusal":
            # The model declined. A different path, never a blind retry.
            return escalate("model refused")

        # Anything else: stop_sequence, context window exceeded, a value that does not exist yet.
        return escalate("unhandled stop_reason " + str(reply.stop_reason))

    # The for loop ran out. The case is still open. A human takes it, with the reason.
    return escalate("budget exhausted")


if __name__ == "__main__":
    print("# E7 · agent loop · " + ("DRY_RUN" if DRY_RUN else "LIVE") + " · scenario=" + SCENARIO + " · BUDGET=" + str(BUDGET))
    print(investigate())
