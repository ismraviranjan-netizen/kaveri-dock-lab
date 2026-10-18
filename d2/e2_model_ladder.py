# E2 · The model ladder: write the bar first, then test  (objective 2.1)
#
#   The bar (accuracy, latency, cost) is written down BEFORE any model is tested. A golden set of hand-sorted
#   tickets is the exam. Fable sits the exam; its token counts are then priced on every rung of the ladder.
#   The rule: buy the cheapest model that passes the bar. Fable is the ceiling, not the default.
#
# Run on battery:  DRY_RUN=1 python e2_model_ladder.py       Run live:  python e2_model_ladder.py

import time
from common import create_message, text_of, PRICE, FX, MODEL, DRY_RUN

BAR = {"exact": 0.92, "p95": 2.0, "cost": 6.0}      # accuracy >= 92%, p95 <= 2 s, <= Rs 6 per call
GOLDEN = [                                            # the golden set: tickets sorted by hand (Kaveri's has 200)
    ("KF-2481 held at customs, e-way bill mismatch", "customs_hold"),
    ("KF-2502 driver cannot find the house", "address_fail"),
    ("KF-2517 carton crushed, two bottles broken", "damage"),
    ("KF-2533 truck stuck in traffic, ETA +6 hours", "delay"),
    ("KF-2540 customs wants the invoice copy first", "customs_hold"),
    ("KF-2558 pincode does not match the street", "address_fail"),
]
SYSTEM = "Name the exception type. Reply with one word only: customs_hold, address_fail, damage or delay."


if __name__ == "__main__":
    print("# E2 · model ladder · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))
    print("bar (written first): exact >= " + format(BAR["exact"], ".0%") + " | p95 <= " + str(BAR["p95"]) + " s | <= Rs " + str(BAR["cost"]) + " per call")

    # STEP 1. Sit the exam: one call per golden ticket, clock on each.
    print()
    print("=== the golden set on " + MODEL + " ===")
    hits, secs, n_in, n_out = 0, [], 0, 0
    for text, label in GOLDEN:
        started = time.perf_counter()
        reply = create_message(model=MODEL, max_tokens=1024, system=SYSTEM,
                               messages=[{"role": "user", "content": text}], output_config={"effort": "low"})
        secs.append(time.perf_counter() - started)
        answer = text_of(reply).lower()
        ok = answer == label
        hits += ok
        n_in += reply.usage.input_tokens
        n_out += reply.usage.output_tokens
        print("  " + ("ok  " if ok else "MISS") + " " + text[:46].ljust(46) + " -> " + answer.ljust(13) + format(secs[-1], ".1f") + " s")

    # STEP 2. The three numbers the bar names.
    exact = hits / len(GOLDEN)
    p95 = sorted(secs)[max(0, round(0.95 * len(secs)) - 1)]     # 95 in every 100 calls are faster than this
    avg_in, avg_out = n_in / len(GOLDEN), n_out / len(GOLDEN)
    print()
    print("  exact " + format(exact, ".0%") + " | p95 " + format(p95, ".1f") + " s | average tokens per call: "
          + format(avg_in, ".0f") + " in, " + format(avg_out, ".0f") + " out")

    # STEP 3. Price those tokens on every rung. Rough: tokenizers differ by model, the SHAPE is the point.
    print()
    print("=== the ladder, Fable's tokens priced on each rung ===")
    cost = {}
    for model, (usd_in, usd_out) in PRICE.items():
        cost[model] = (avg_in * usd_in + avg_out * usd_out) / 1e6 * FX
        print("  " + model.ljust(20) + " Rs " + format(cost[model], ".3f") + " per call" + ("   <- this run" if model == MODEL else ""))

    # STEP 4. The verdict is code: three comparisons against the bar.
    checks = {"exact": exact >= BAR["exact"], "p95": p95 <= BAR["p95"], "cost": cost[MODEL] <= BAR["cost"]}
    failed = [name for name, ok in checks.items() if not ok]
    print()
    print("verdict for " + MODEL + ": " + ("PASS" if not failed else "FAIL on " + ", ".join(failed)))
    print("next: run the golden set on the cheaper rungs; buy the cheapest model that passes the bar")
