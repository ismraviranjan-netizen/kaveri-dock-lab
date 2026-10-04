# E3 · Routing: a cheap nurse at the door, specialist wards behind it  (objective 1.3b, workflow 2)
#
#   Nurse:  one cheap call says ONE word: which kind of problem is this?   (E2's classify + gate, reused)
#   Table:  the word picks WHICH specialist, and which MODEL, handles the email.
#   Ward:   ONE call to that specialist. It never saw a menu. The code chose.
# Routing is where model selection stops being one decision and becomes a decision PER category.
#
# Run on battery:  DRY_RUN=1 python e3_routing.py           Run live:  python e3_routing.py

from common import ask, MODEL_MAIN, MODEL_SMALL, EMAIL, DRY_RUN
from e2_chaining import classify, gate          # reuse E2's nurse and checklist


# ---------------------------------------------------------------
# STEP 0. The wards. Each category maps to (which model, the ward's instructions).
#         This table IS the router. Add a ward by adding a row. No model is involved in the choice.
# ---------------------------------------------------------------

SPECIALISTS = {
    "refund":  (MODEL_MAIN,  "You resolve refund disputes at Kaveri Freight. Acknowledge, say what you will verify, never promise money."),
    "customs": (MODEL_MAIN,  "You explain customs holds and next steps for Indian import consignments at Kaveri Freight."),
    "delay":   (MODEL_SMALL, "You write short delay apologies for Kaveri Freight with a new ETA. Under 80 words."),
}
# Production would put the refund ward on the Opus tier. MODEL_MAIN is Sonnet here to keep learning runs cheap.

# If the nurse says a word that has no ward (for example "address"), send it here instead of crashing.
DEFAULT_WARD = "delay"


# ---------------------------------------------------------------
# STEP 1. Table lookup: plain Python. An unmapped word goes to a safe ward, not a KeyError at 2 a.m.
# ---------------------------------------------------------------

def pick_ward(category):
    if category in SPECIALISTS:
        return category
    return DEFAULT_WARD


# ---------------------------------------------------------------
# STEP 2. The router: email in, specialist's reply out.
# ---------------------------------------------------------------

def route(email_text):
    # 2a. The nurse looks once and says one word. The gate checks it.
    category = gate(classify(email_text))

    # 2b. The word picks the ward; the ward brings its own model and instructions.
    ward = pick_ward(category)
    model, instructions = SPECIALISTS[ward]
    print("Nurse said:", repr(category), "-> ward:", ward, "-> model:", model)

    # 2c. ONE call to the chosen specialist. Its instructions go in the system prompt.
    return ask(model, email_text, system=instructions)


if __name__ == "__main__":
    print("# E3 · routing · " + ("DRY_RUN" if DRY_RUN else "LIVE"))

    # STEP 3. Route Padma's email.
    print("=== Routing Padma's email ===")
    specialist_reply = route(EMAIL)
    print()
    print("Specialist wrote:")
    print(specialist_reply)

    # STEP 4. Show the default ward. No model call: just the table lookup.
    print()
    print("=== A word with no ward ===")
    word = "address"
    ward = pick_ward(word)
    print(repr(word), "has no ward, so it goes to", repr(ward), "on model", SPECIALISTS[ward][0])
