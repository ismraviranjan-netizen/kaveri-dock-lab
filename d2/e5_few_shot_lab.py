# E5 · Few-shot lab: none, three or twelve examples?  (objective 2.3)
#
#   Examples sit in the system prompt and are paid for on EVERY call. The lab runs the same six test tickets
#   with 0, 3 and 12 examples, and prints accuracy against input tokens, scaled to a day of Desk calls.
#   Pick the fewest examples that clear your bar. The examples never come from the test set.
#
# Run on battery:  DRY_RUN=1 python e5_few_shot_lab.py       Run live:  python e5_few_shot_lab.py

from common import create_message, text_of, IN_USD, FX, DESK_CALLS_PER_DAY, MODEL, DRY_RUN

SHOTS = [                                 # 12 examples, 3 per type, never taken from the test set
    ("Bill of entry pending at JNPT", "customs_hold"),
    ("Flat number missing on the label", "address_fail"),
    ("Seal broken, pallet wet", "damage"),
    ("Ghat road closed by a landslide", "delay"),
    ("Customs wants the HSN code fixed", "customs_hold"),
    ("Consignee moved, no new address", "address_fail"),
    ("Glass jars cracked in transit", "damage"),
    ("Driver resting, ETA tomorrow", "delay"),
    ("Duty unpaid, cargo held at the ICD", "customs_hold"),
    ("Gate locked, nobody answers", "address_fail"),
    ("Box crushed at one corner", "damage"),
    ("Vessel late, port congestion", "delay"),
]
TEST = [
    ("KF-2481 held at customs, e-way bill mismatch", "customs_hold"),
    ("KF-2502 driver cannot find the house", "address_fail"),
    ("KF-2517 two bottles broken on arrival", "damage"),
    ("KF-2533 truck stuck in traffic, ETA +6 hours", "delay"),
    ("KF-2540 invoice copy needed before release", "customs_hold"),
    ("KF-2558 pincode does not match the street", "address_fail"),
]
RULE = "Name the exception type. Reply with one word only: customs_hold, address_fail, damage or delay."


def system_for(k):
    """The rule alone, or the rule plus the first k examples, each inside <example> tags."""
    if not k:
        return RULE
    shots = ["<example>" + text + " -> " + label + "</example>" for text, label in SHOTS[:k]]
    return RULE + "\n<examples>\n" + "\n".join(shots) + "\n</examples>"


if __name__ == "__main__":
    print("# E5 · few-shot lab · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL) + " · " + str(len(TEST)) + " test tickets x 3 settings")
    print()
    print("  " + "examples".rjust(8) + "input tokens".rjust(14) + "accuracy".rjust(10) + ("Rs/day, " + format(DESK_CALLS_PER_DAY, ",") + " calls").rjust(22))
    for k in (0, 3, 12):
        hits, tokens = 0, 0
        for text, label in TEST:
            reply = create_message(model=MODEL, max_tokens=1024, system=system_for(k),
                                   messages=[{"role": "user", "content": text}], output_config={"effort": "low"})
            hits += text_of(reply).lower() == label
            tokens += reply.usage.input_tokens
        per_call = tokens / len(TEST)
        day = per_call * IN_USD * FX * DESK_CALLS_PER_DAY            # input side only
        print("  " + str(k).rjust(8) + format(per_call, ",.0f").rjust(14) + format(hits / len(TEST), ".0%").rjust(10) + format(day, ",.0f").rjust(22))
    print()
    print("pick the fewest examples that clear your bar: every example is paid for on every call")
