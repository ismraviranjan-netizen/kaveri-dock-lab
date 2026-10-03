# E2 · Prompt chaining — the assembly line with a supervisor's checklist (objective 1.3b, workflow 1)
# classify -> gate -> draft. Your code owns the order forever. The gate is code, not model.
from common import ask, MODEL_SMALL, MODEL_MAIN, EMAIL, DRY_RUN

VALID = {"delay", "damage", "customs", "refund", "address", "other"}   # the laminated checklist

def classify(email):                                   # step 1: small, cheap, focused
    out = ask(MODEL_SMALL, "One word, the category only: " + email)
    return out.strip().lower()

def gate(category):                                    # the checklist between desks
    if category not in VALID:                          # malformed -> stop the line
        raise ValueError(f"bad category: {category}")
    return category

def draft_reply(email, category):                      # step 2: sees step 1's output
    return ask(MODEL_MAIN,
               f"A {category} exception. Draft a courteous reply, under 120 words, "
               f"no promises about compensation:\n" + email)

if __name__ == "__main__":
    print(f"# E2 · prompt chaining · {'DRY_RUN' if DRY_RUN else 'LIVE'}")
    cat = classify(EMAIL);              print(f"# desk 1 classify -> {cat!r}")
    cat = gate(cat);                    print(f"# gate            -> {cat!r} is in VALID, line continues")
    reply = draft_reply(EMAIL, cat);    print(f"# desk 2 draft    -> {len(reply.split())} words")
    print(reply)
    print("\n# sabotage: what the gate does with a mumbled category")
    try:
        gate("customs-ish")
    except ValueError as e:
        print(f"# gate raised ValueError: {e}  <- the line stopped; desk 2 never wrote to a nonsense category")
