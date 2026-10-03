# E3 · Routing — the hospital triage nurse: cheap sort at the door, specialist wards behind it (objective 1.3b, workflow 2)
# Routing is where model selection stops being one decision and becomes a decision per category.
from common import ask, MODEL_MAIN, MODEL_MID, MODEL_SMALL, EMAIL, DRY_RUN
from e2_chaining import classify, gate                 # reuse E2's nurse and checklist

SPECIALISTS = {
    "refund":  (MODEL_MAIN,  "You resolve refund disputes. Cap: acknowledge, verify, never promise."),
    "customs": (MODEL_MID,   "You explain customs holds and next steps for Indian import consignments."),
    "delay":   (MODEL_SMALL, "You write short delay apologies with the new ETA."),
}

def route(email):
    cat = gate(classify(email))                         # one word decides the ward
    model, system = SPECIALISTS.get(cat, SPECIALISTS["delay"])   # unmapped -> a safe ward, not a KeyError at 2 a.m.
    print(f"# nurse says {cat!r} -> ward model {model}")
    return ask(model, system + "\n\n" + email)          # one call, one specialist; the model never saw a menu

if __name__ == "__main__":
    print(f"# E3 · routing · {'DRY_RUN' if DRY_RUN else 'LIVE'}")
    print(route(EMAIL))
    print("\n# the default ward: an unmapped category falls to 'delay' instead of crashing")
    model, _ = SPECIALISTS.get("address", SPECIALISTS["delay"])
    print(f"# 'address' is not a ward -> {model}")
