# e8_watchman.py — the street: canary bars, drift alarms, and an owner for every alert
import math

def p95(xs):
    s = sorted(xs)
    return s[math.ceil(0.95 * len(s)) - 1]

BARS = {"p95_s": 2.0, "override_rate": 0.02, "cost_inr": 6.00}       # the gate's own bars
OWNER = {"p95_s": "Arjun", "override_rate": "Meera", "cost_inr": "Devika", "quality": "Meera"}

def canary(window):                             # 5% of traffic, 48 h: any red bar rolls back
    reds = [k for k, bar in BARS.items() if window[k] > bar]
    return f"ROLLBACK {reds}" if reds else "PROMOTE to 25%"

def drift(days, drop_pts=3.0, streak_days=2):   # the slow rot no single day shows
    alarms, streak, worst = [], 0, 0
    for d in days:
        streak = streak + 1 if d["p95_s"] > BARS["p95_s"] else 0
        worst = max(worst, streak)
    week = [d["quality"] for d in days[-7:]]
    if week[0] - week[-1] >= drop_pts:
        alarms.append(("quality", f"{week[0]:.1f} -> {week[-1]:.1f} over 7 days"))
    if worst >= streak_days:
        alarms.append(("p95_s", f"over {BARS['p95_s']} s for {worst} days running"))
    return alarms

if __name__ == "__main__":
    print("canary 16-18 Oct:", canary({"p95_s": 1.7, "override_rate": 0.011, "cost_inr": 4.12}))
    lat = [0.4] * 60 + [0.7] * 25 + [1.1] * 9 + [2.3] * 6            # one afternoon, 100 replies
    print(f"afternoon: mean {sum(lat) / len(lat):.2f} s   p95 {p95(lat):.1f} s")
    week = [{"quality": q, "p95_s": p} for q, p in zip(
        [93.8, 93.6, 93.1, 92.4, 91.9, 91.2, 90.6], [1.6, 1.7, 1.8, 1.9, 2.1, 2.3, 2.4])]
    for metric, msg in drift(week):
        print(f"ALERT {metric}: {msg} -> {OWNER[metric]} · freeze releases, open the traces")
