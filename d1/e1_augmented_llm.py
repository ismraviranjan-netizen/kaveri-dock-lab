# E1 · The augmented LLM: KAVI triages one exception  (objective 1.3a, the cell every organism is built from)
#
# One call, one tool, at most one round-trip. The model may ask us to look the shipment up.
# If it does, we run the lookup and send the fact back. Then it answers.
#
# Run on battery:  DRY_RUN=1 python e1_augmented_llm.py      (Windows:  set DRY_RUN=1  first)
# Run live:        python e1_augmented_llm.py                (needs ANTHROPIC_API_KEY, see common.py)

import json
from common import make_client, trace, text_of, fake_status, MODEL_MAIN, MAX_TOKENS, EMAIL, TOOLS_KAVERI, DRY_RUN


# ---------------------------------------------------------------
# STEP 0. Things we decide before talking to the model
#         (MODEL_MAIN, MAX_TOKENS and EMAIL come from common.py)
# ---------------------------------------------------------------

# The ONE tool the model is allowed to ask for. This is only a description: name, what it does,
# what input it needs. The model cannot run it. We run it.
TOOLS = [TOOLS_KAVERI[0]]                 # get_shipment_status

# The instructions taped to the model's desk.
SYSTEM = (
    "You triage Kaveri shipment exceptions. "
    "Reply as JSON {category, urgency} and nothing else. "
    "Categories: delay, damage, customs, refund, address, other."
)

# STEP 1. The tool itself lives in common.py as fake_status(): plain Python. The model never sees it.


def triage(email_text):

    # STEP 2. Connect. DRY_RUN=1 gives the scripted stand-in; otherwise the real SDK.
    client = make_client()

    # STEP 3. Start the conversation with one message: the email. This is page 1 of the case file.
    conversation = []
    conversation.append({"role": "user", "content": email_text})

    # STEP 4. First call to the model.
    reply = client.messages.create(
        model=MODEL_MAIN,
        max_tokens=MAX_TOKENS,
        system=SYSTEM,
        tools=TOOLS,
        messages=conversation,
    )
    trace(1, reply)                       # prints:  # turn 1  stop_reason=...  (tool names)

    # STEP 5. Did the model ask for the tool?  "tool_use" means: "I need a lookup before I can answer."
    if reply.stop_reason == "tool_use":

        # 5a. Find the tool request inside the reply. A reply is a list of blocks.
        tool_request = None
        for block in reply.content:
            if block.type == "tool_use":
                tool_request = block
                break

        # 5b. Run the tool ourselves, with the input the model filled in.
        consignment_id = tool_request.input["consignment_id"]
        lookup_result = fake_status(consignment_id)

        # 5c. Add the model's own request to the conversation: page 2.
        #     The API remembers nothing between calls, so we must send its own words back.
        conversation.append({"role": "assistant", "content": reply.content})

        # 5d. Add the tool's answer: page 3. It is tagged with the request's id so the model knows
        #     which question this answers. The API wants text, so the dict becomes a JSON string.
        tool_answer = {
            "type": "tool_result",
            "tool_use_id": tool_request.id,
            "content": json.dumps(lookup_result),
        }
        conversation.append({"role": "user", "content": [tool_answer]})

        # 5e. Second call. Same five arguments. The conversation is now 3 pages long.
        reply = client.messages.create(
            model=MODEL_MAIN,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            tools=TOOLS,
            messages=conversation,
        )
        trace(2, reply)

    # STEP 6. Read the final answer. A refusal is not an answer; otherwise collect the text blocks only.
    if reply.stop_reason == "refusal":
        return "The model declined to answer."
    return text_of(reply)


if __name__ == "__main__":
    if DRY_RUN:
        print("# E1 · augmented LLM · DRY_RUN: scripted stand-in, 0 paid calls")
    else:
        print("# E1 · augmented LLM · LIVE · " + MODEL_MAIN)
    print(triage(EMAIL))
