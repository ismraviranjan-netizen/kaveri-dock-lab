# e3_live.py
# E3: routing. A triage nurse at the door, specialist wards behind it.
#   Nurse:  one cheap call says ONE word: which kind of problem is this?
#   Gate:   plain Python checks the word is on the list.
#   Ward:   the word picks WHICH specialist (and which model) handles the email. One call.
# The model that answers the customer never saw a menu. The code chose the ward.
#
# Before running:   pip install anthropic   and   ANTHROPIC_API_KEY in the environment
# Run:              python e3_live.py

import anthropic


# ---------------------------------------------------------------
# STEP 0. Things we decide before talking to the model
# ---------------------------------------------------------------

MAX_TOKENS = 1024

# Three model sizes. Routing is where "which model" becomes a decision PER category.
MODEL_BIG = "claude-sonnet-5-5"       # for money decisions (refunds). In production: the Opus tier.
MODEL_MID = "claude-sonnet-5-5"       # for explanations (customs)
MODEL_SMALL = "claude-haiku-4-5"      # for short templated notes (delay apologies) and the nurse

EMAIL = """Subject: KF-2481 - where is my shipment?? Three days late!

Hello Kaveri,

My consignment KF-2481 (Pune to Chennai, 12 cartons of textile samples) was promised on Monday. It is now Thursday. Your portal says "in transit" and nothing else. My buyer is threatening to cancel the order.

Where is it right now, and what are you doing about it?

- Padma Deshmukh
"""

VALID_CATEGORIES = {"delay", "damage", "customs", "refund", "address", "other"}

# The wards. Each category maps to (which model, what instructions).
# This table IS the router. Add a ward by adding a row. No model is involved in the choice.
SPECIALISTS = {
    "refund":  (MODEL_BIG,   "You resolve refund disputes at Kaveri Freight. Acknowledge, say what you will verify, never promise money."),
    "customs": (MODEL_MID,   "You explain customs holds and next steps for Indian import consignments at Kaveri Freight."),
    "delay":   (MODEL_SMALL, "You write short delay apologies for Kaveri Freight with a new ETA. Under 80 words."),
}

# If the nurse says a word that has no ward (for example "address"), send it here instead of crashing.
DEFAULT_WARD = "delay"


# ---------------------------------------------------------------
# STEP 1. Connect, and one helper: ask a model a question, get text back.
#         This time the helper takes the MODEL as an argument, because each ward uses a different one.
# ---------------------------------------------------------------

client = anthropic.Anthropic()

def ask(model, question):
    reply = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": question}],
    )
    if reply.stop_reason == "refusal":
        raise RuntimeError("The model declined to answer.")
    answer = ""
    for block in reply.content:
        if block.type == "text":
            answer = answer + block.text
    return answer.strip()


# ---------------------------------------------------------------
# STEP 2. The nurse (same as E2's desk 1) and the gate (same as E2's gate).
# ---------------------------------------------------------------

def classify(email_text):
    question = (
        "Read this customer email and reply with ONE word only, the category of the problem. "
        "Choose from: delay, damage, customs, refund, address, other. "
        "No explanation, no punctuation, just the word.\n\n"
        + email_text
    )
    return ask(MODEL_SMALL, question).lower()

def gate(category):
    if category not in VALID_CATEGORIES:
        raise ValueError("Bad category from the nurse: " + repr(category))
    return category


# ---------------------------------------------------------------
# STEP 3. The router: word in, specialist reply out.
# ---------------------------------------------------------------

def route(email_text):
    # 3a. The nurse looks once and says one word.
    category = gate(classify(email_text))

    # 3b. Plain Python looks the word up in the table. .get() with a default means
    #     an unmapped word goes to a safe ward instead of raising KeyError at 2 a.m.
    if category in SPECIALISTS:
        model, instructions = SPECIALISTS[category]
    else:
        model, instructions = SPECIALISTS[DEFAULT_WARD]

    print("Nurse said:", repr(category))
    print("Routed to ward:", category if category in SPECIALISTS else DEFAULT_WARD, "using model:", model)

    # 3c. ONE call to the chosen specialist. It gets its own instructions plus the email.
    return ask(model, instructions + "\n\n" + email_text)


# ---------------------------------------------------------------
# STEP 4. Run it.
# ---------------------------------------------------------------

print("=== Routing Padma's email ===")
specialist_reply = route(EMAIL)
print()
print("Specialist wrote:")
print(specialist_reply)


# ---------------------------------------------------------------
# STEP 5. Show the default ward. No model call: just the table lookup.
# ---------------------------------------------------------------

print()
print("=== What happens to a word with no ward ===")
word = "address"
if word in SPECIALISTS:
    chosen = word
else:
    chosen = DEFAULT_WARD
print(repr(word), "has no ward, so it goes to", repr(chosen), "using model", SPECIALISTS[chosen][0])
