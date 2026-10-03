# e2_live.py
# E2: prompt chaining. Two desks in a fixed order, with a checklist between them.
#   Desk 1: read the email, say ONE word: what kind of problem is this?
#   Gate:   plain Python checks that word is on the approved list. If not, stop.
#   Desk 2: knowing the category, write a short courteous reply.
# The CODE decides the order. The model never gets to change it.
#
# Before running:   pip install anthropic
#                   put ANTHROPIC_API_KEY in your environment (or in a git-ignored .env file)
# Run:              python e2_live.py

import anthropic


# ---------------------------------------------------------------
# STEP 0. Things we decide before talking to the model
# ---------------------------------------------------------------

MODEL = "claude-sonnet-5-5"       # one model for both desks, to keep it simple
MAX_TOKENS = 1024

# The customer's email. Same one as E1.
EMAIL = """Subject: KF-2481 - where is my shipment?? Three days late!

Hello Kaveri,

My consignment KF-2481 (Pune to Chennai, 12 cartons of textile samples) was promised on Monday. It is now Thursday. Your portal says "in transit" and nothing else. My buyer is threatening to cancel the order.

Where is it right now, and what are you doing about it?

- Padma Deshmukh
"""

# The laminated checklist on the wall between the two desks.
# Only these six words are allowed to pass from desk 1 to desk 2.
VALID_CATEGORIES = {"delay", "damage", "customs", "refund", "address", "other"}


# ---------------------------------------------------------------
# STEP 1. Connect to the API. The key is read from ANTHROPIC_API_KEY.
# ---------------------------------------------------------------

client = anthropic.Anthropic()


# ---------------------------------------------------------------
# STEP 2. A small helper: send one question, get the text back.
#         No tools here. E2 is text in, text out, twice.
# ---------------------------------------------------------------

def ask(question):
    reply = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": question}],
    )

    # If the model declined, do not pretend the empty text is an answer.
    if reply.stop_reason == "refusal":
        raise RuntimeError("The model declined to answer.")

    # Collect only the text blocks. Skip thinking blocks or anything else.
    answer = ""
    for block in reply.content:
        if block.type == "text":
            answer = answer + block.text

    return answer.strip()


# ---------------------------------------------------------------
# STEP 3. DESK 1: classify. One word only.
# ---------------------------------------------------------------

def classify(email_text):
    question = (
        "Read this customer email and reply with ONE word only, the category of the problem. "
        "Choose from: delay, damage, customs, refund, address, other. "
        "No explanation, no punctuation, just the word.\n\n"
        + email_text
    )
    word = ask(question)
    return word.lower()           # make "Customs" and "customs" the same thing


# ---------------------------------------------------------------
# STEP 4. THE GATE: plain Python, no model.
#         If desk 1 mumbled something that is not on the checklist, stop the line here.
# ---------------------------------------------------------------

def gate(category):
    if category not in VALID_CATEGORIES:
        raise ValueError("Bad category from desk 1: " + repr(category))
    return category


# ---------------------------------------------------------------
# STEP 5. DESK 2: draft the reply. It is TOLD the category; it does not re-decide it.
# ---------------------------------------------------------------

def draft_reply(email_text, category):
    question = (
        "This is a " + category + " exception at Kaveri Freight. "
        "Draft a courteous reply to the customer, under 120 words. "
        "Do not promise any refund or compensation.\n\n"
        + email_text
    )
    return ask(question)


# ---------------------------------------------------------------
# STEP 6. Run the line, in the order the code fixes: classify -> gate -> draft.
# ---------------------------------------------------------------

print("=== Desk 1: classify ===")
category = classify(EMAIL)
print("Desk 1 said:", repr(category))

print()
print("=== Gate: check the word against the list ===")
category = gate(category)
print("Gate passed:", category, "is on the approved list. Line continues.")

print()
print("=== Desk 2: draft ===")
reply = draft_reply(EMAIL, category)
word_count = len(reply.split())
print("Desk 2 wrote", word_count, "words:")
print()
print(reply)


# ---------------------------------------------------------------
# STEP 7. Sabotage test. What happens if desk 1 had mumbled?
#         No model call here. We hand the gate a bad word on purpose.
# ---------------------------------------------------------------

print()
print("=== Sabotage: feed the gate a word that is not on the list ===")
try:
    gate("customs-ish")
except ValueError as error:
    print("Gate stopped the line:", error)
    print("Desk 2 was never called. No reply was written for a nonsense category.")
