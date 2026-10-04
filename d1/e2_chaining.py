# E2 · Prompt chaining: two desks in a fixed order, a checklist between them  (objective 1.3b, workflow 1)
#
#   Desk 1: read the email, say ONE word: what kind of problem is this?
#   Gate:   plain Python checks that word is on the approved list. If not, stop the line.
#   Desk 2: knowing the category, write a short courteous reply.
# The CODE decides the order. The model never gets to change it. That is Law 2.
#
# Run on battery:  DRY_RUN=1 python e2_chaining.py          Run live:  python e2_chaining.py

from common import ask, MODEL_SMALL, MODEL_MAIN, EMAIL, DRY_RUN


# ---------------------------------------------------------------
# STEP 0. The laminated checklist on the wall between the two desks.
#         Only these six words are allowed to pass from desk 1 to desk 2.
# ---------------------------------------------------------------

VALID_CATEGORIES = {"delay", "damage", "customs", "refund", "address", "other"}


# ---------------------------------------------------------------
# STEP 1. DESK 1: classify. One word only, on the small model.
# ---------------------------------------------------------------

def classify(email_text):
    question = (
        "Read this customer email and reply with ONE word only, the category of the problem. "
        "Choose from: delay, damage, customs, refund, address, other. "
        "No explanation, no punctuation, just the word.\n\n"
        + email_text
    )
    word = ask(MODEL_SMALL, question)
    return word.lower()                   # "Customs" and "customs" become the same thing


# ---------------------------------------------------------------
# STEP 2. THE GATE: plain Python. No model, no cost.
#         If desk 1 mumbled something that is not on the checklist, stop the line here.
# ---------------------------------------------------------------

def gate(category):
    if category not in VALID_CATEGORIES:
        raise ValueError("bad category: " + category)
    return category


# ---------------------------------------------------------------
# STEP 3. DESK 2: draft the reply. It is TOLD the category; it does not re-decide it.
# ---------------------------------------------------------------

def draft_reply(email_text, category):
    question = (
        "This is a " + category + " exception at Kaveri Freight. "
        "Draft a courteous reply to the customer, under 120 words. "
        "Do not promise any refund or compensation.\n\n"
        + email_text
    )
    return ask(MODEL_MAIN, question)


if __name__ == "__main__":
    print("# E2 · prompt chaining · " + ("DRY_RUN" if DRY_RUN else "LIVE"))

    # STEP 4. Run the line in the order the code fixes: classify -> gate -> draft.
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
    print("Desk 2 wrote", len(reply.split()), "words:")
    print()
    print(reply)

    # STEP 5. Sabotage test: hand the gate a word that is not on the list. No model call here.
    print()
    print("=== Sabotage: feed the gate a word that is not on the list ===")
    try:
        gate("customs-ish")
    except ValueError as error:
        print("Gate stopped the line:", error)
        print("Desk 2 was never called. No reply was written for a nonsense category.")
