# e7_levers.py — the price of the verdict: green first, then levers that print a number
BAR = 0.92                                                     # the triage bar (Law 2)
EVAL = {"haiku_easy": 0.93, "haiku_hard": 0.81}                # golden-set triage, by slice
COST = {"sonnet_easy": 5.45, "sonnet_hard": 7.20, "haiku_easy": 3.20}  # ₹ all-in, 30 days
ROUTER, MIX = 0.10, {"easy": 0.80, "hard": 0.20}
MIN_CACHE = {"claude-sonnet-5-5": 512, "claude-haiku-4-5-20251001": 4096}

def routed(slice_):                                            # promote only past the bar
    return EVAL[f"haiku_{slice_}"] >= BAR

before = MIX["easy"] * COST["sonnet_easy"] + MIX["hard"] * COST["sonnet_hard"]
after = (ROUTER + MIX["easy"] * COST["haiku_easy"] + MIX["hard"] * COST["sonnet_hard"]
         if routed("easy") else before)
print(f"easy -> Haiku: {routed('easy')}   hard -> Haiku: {routed('hard')}")
print(f"₹ per exception {before:.2f} -> {after:.2f}   (ceiling 6.00)")

def billed_input(prefix, varying, cached, hit, read=0.10, write=1.25):
    if not cached:
        return prefix + varying                                # base-price token-equivalents
    return prefix * (read if hit else write) + varying

for model, prefix in [("claude-sonnet-5-5", 9200), ("claude-haiku-4-5-20251001", 9200),
                      ("claude-haiku-4-5-20251001", 900)]:
    print(f"{model:<26} prefix {prefix:>5}  cacheable {prefix >= MIN_CACHE[model]}")
print("input billed per call   none {:.0f}   miss {:.0f}   hit {:.0f}".format(
      billed_input(9200, 1800, False, False), billed_input(9200, 1800, True, False),
      billed_input(9200, 1800, True, True)))
