# e4_calibrate.py — weigh the scale before it weighs anything (Law 3)
import json
from collections import defaultdict

GATE_OVERALL, GATE_CATEGORY, MIN_N = 0.90, 0.85, 10

def agreement(rows):                  # rows: {"cat", "human", "judge"}; UNKNOWN goes to a human
    decided = [r for r in rows if r["judge"] != "UNKNOWN"]
    by = defaultdict(lambda: [0, 0])
    for r in decided:
        by[r["cat"]][0] += r["judge"] == r["human"]
        by[r["cat"]][1] += 1
    overall = sum(a for a, _ in by.values()) / len(decided)
    return overall, by, len(rows) - len(decided)

def report(name, rows):
    overall, by, unknown = agreement(rows)
    ok = overall >= GATE_OVERALL
    print(f"{name}: overall {overall:.0%} on {sum(n for _, n in by.values())} decided"
          f" (+{unknown} UNKNOWN -> human)  {'PASS' if ok else 'FAIL'}")
    for cat, (a, n) in sorted(by.items()):
        flag = ("UNDER-SAMPLED" if n < MIN_N else
                "ok" if a / n >= GATE_CATEGORY else "FAIL")
        ok = ok and flag != "FAIL"
        print(f"   {cat:<16}{a:>3}/{n:<3}{a / n:>6.0%}   {flag}")
    return ok

if __name__ == "__main__":
    sat = json.load(open("calib_sat_40.json"))       # Meera's team labelled 40, blind
    fri = json.load(open("calib_fri_52.json"))       # the same 40 + 12 confident-but-wrong
    report("Saturday", sat)
    report("Friday  ", fri)
