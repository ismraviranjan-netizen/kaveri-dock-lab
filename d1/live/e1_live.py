# e1_live.py
# E1: ask the model to sort one customer email into a category.
# The model may ask us to look up the shipment first. If it does, we look it up and tell it the answer.
#
# Before running:   pip install anthropic
#                   put ANTHROPIC_API_KEY in your environment (or in a .env file that is git-ignored)
# Run:              python e1_live.py

import json
import anthropic


# ---------------------------------------------------------------
# STEP 0. Things we decide before talking to the model
# ---------------------------------------------------------------

MODEL = "claude-sonnet-5-5"       # which model answers
MAX_TOKENS = 1024                  # the longest reply we will accept

# The customer's email. This is the only input.
EMAIL = """Subject: KF-2481 - where is my shipment?? Three days late!

Hello Kaveri,

My consignment KF-2481 (Pune to Chennai, 12 cartons of textile samples) was promised on Monday. It is now Thursday. Your portal says "in transit" and nothing else. My buyer is threatening to cancel the order.

Where is it right now, and what are you doing about it?

- Padma Deshmukh
"""

# The instructions we tape to the model's desk.
SYSTEM = (
    "You triage Kaveri shipment exceptions. "
    "Reply as JSON {category, urgency}. "
    "Categories: delay, damage, customs, refund, address, other."
)

# A description of ONE tool the model is allowed to ask for.
# This is only a description. The model cannot run it. We run it.
TOOLS = [
    {
        "name": "get_shipment_status",
        "description": "Live status for one Kaveri consignment id (e.g. KF-2481).",
        "input_schema": {
            "type": "object",
            "properties": {"consignment_id": {"type": "string"}},
            "required": ["consignment_id"],
        },
    }
]


# ---------------------------------------------------------------
# STEP 1. The tool itself. Plain Python. The model never sees this code.
#         In real life this would read the depot database.
# ---------------------------------------------------------------

def get_shipment_status(consignment_id):
    return {
        "id": consignment_id,
        "status": "CUSTOMS_HOLD",
        "missing": "e-way bill",
        "days_late": 3,
    }


# ---------------------------------------------------------------
# STEP 2. Connect to the API. The key is read from ANTHROPIC_API_KEY.
# ---------------------------------------------------------------

client = anthropic.Anthropic()


# ---------------------------------------------------------------
# STEP 3. Start the conversation with one message: the email.
# ---------------------------------------------------------------

conversation = []
conversation.append({"role": "user", "content": EMAIL})


# ---------------------------------------------------------------
# STEP 4. First call to the model.
# ---------------------------------------------------------------

reply = client.messages.create(
    model=MODEL,
    max_tokens=MAX_TOKENS,
    system=SYSTEM,
    tools=TOOLS,
    messages=conversation,
)

print("Turn 1 finished because:", reply.stop_reason)


# ---------------------------------------------------------------
# STEP 5. Did the model ask for the tool?
#         "tool_use" means: "I need a lookup before I can answer."
# ---------------------------------------------------------------

if reply.stop_reason == "tool_use":

    # 5a. Find the tool request inside the reply.
    #     A reply is a list of blocks. We want the block whose type is "tool_use".
    tool_request = None
    for block in reply.content:
        if block.type == "tool_use":
            tool_request = block
            break

    print("Model asked for tool:", tool_request.name)
    print("With input:", tool_request.input)

    # 5b. Run the tool ourselves, with the input the model filled in.
    consignment_id = tool_request.input["consignment_id"]
    lookup_result = get_shipment_status(consignment_id)
    print("Tool returned:", lookup_result)

    # 5c. Add the model's own request to the conversation.
    #     The API remembers nothing between calls, so we must send its own words back.
    conversation.append({"role": "assistant", "content": reply.content})

    # 5d. Add the tool's answer to the conversation, tagged with the request's id,
    #     so the model knows which question this answers.
    tool_answer = {
        "type": "tool_result",
        "tool_use_id": tool_request.id,
        "content": json.dumps(lookup_result),     # the API wants text, so turn the dict into a JSON string
    }
    conversation.append({"role": "user", "content": [tool_answer]})

    # 5e. Second call. Same settings. The conversation is now 3 messages long.
    reply = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM,
        tools=TOOLS,
        messages=conversation,
    )

    print("Turn 2 finished because:", reply.stop_reason)


# ---------------------------------------------------------------
# STEP 6. Read the final answer.
# ---------------------------------------------------------------

if reply.stop_reason == "refusal":
    print("The model declined to answer.")
else:
    # Collect only the text blocks. Skip anything else, such as thinking blocks.
    answer = ""
    for block in reply.content:
        if block.type == "text":
            answer = answer + block.text

    print("Final answer:", answer)
