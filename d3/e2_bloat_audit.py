# E2 · The bloat audit: price the belt, then trim it  (objective 3.1, Law 1)
#
#   Every tool's name, description and schema rides along on EVERY request, used or not.
#   Two bills: the token bill (count it) and the confusion bill (lookalike tools, the count cannot see it).
#   count_tokens is a FREE endpoint: pricing the belt costs nothing. On battery, four characters per token.
#
# Run on battery:  DRY_RUN=1 python e2_bloat_audit.py        Run live:  python e2_bloat_audit.py

from common import count_tokens, belt, ALL9, CORE3, DRY_RUN


# ---------------------------------------------------------------
# STEP 0. The two belts and the day's traffic
# ---------------------------------------------------------------

DAILY_CALLS = 40_000                      # one Tuesday at Kaveri
core = belt(CORE3)                        # the old fitter's belt: the three tools the logs say were called


# ---------------------------------------------------------------
# STEP 1. Price one belt. The messages part is a one-word placeholder; the tools are what we are pricing.
# ---------------------------------------------------------------

def price(tools):
    return count_tokens(tools=tools, text="hi")


if __name__ == "__main__":
    print("# E2 · bloat audit · " + ("DRY_RUN (4 chars per token)" if DRY_RUN else "LIVE count_tokens (free endpoint)"))

    # STEP 2. Price both belts.
    nine = price(ALL9)
    three = price(core)
    print(str(len(ALL9)) + " tools: " + str(nine) + " tokens / call")
    print(str(len(core)) + " tools: " + str(three) + " tokens / call")

    # STEP 3. Multiply by the traffic. Bloat is linear in volume.
    tax = (nine - three) * DAILY_CALLS
    print("belt tax: " + format(tax, ",") + " tokens/day for tools the logs say were called 0 times last week")

    # STEP 4. The confusion bill: two lookalike cards side by side. No model call: just read them.
    print()
    print("=== The lookalike pair the token count cannot see ===")
    for tool in belt({"get_shipment_status", "lookup_order"}):
        print("  " + tool["name"] + ": " + tool["description"])
    print("  Trim by the logs, and keep one rare load-bearing tool (escalate_to_human) as cheap insurance.")
