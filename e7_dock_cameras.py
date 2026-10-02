# E7 · The dock cameras — trace ids, then p95 vs mean (objective 3.4)
import json, time, uuid
from collections import defaultdict

def log(**row):
    print(json.dumps(row))

def one_ticket():                               # one live ticket through three stages
    trace = uuid.uuid4().hex[:8]                 # minted ONCE, outside the loop
    total = 0
    for stage, ms, tok, pc in (("route", 10, 400, 1), ("retrieve", 20, 3600, 3), ("draft", 30, 5800, 41)):
        time.sleep(ms / 1000); total += ms
        log(trace=trace, stage=stage, ms=ms, tokens=tok, cost_pc=pc)
    log(trace=trace, stage="total", ms=total)

def p95(xs):
    xs = sorted(xs); return xs[int(0.95 * len(xs)) - 1]

def digest(path="logday.jsonl"):
    series = defaultdict(list)
    for line in open(path):
        r = json.loads(line); series[r["stage"]].append(r["ms"])
    for stage in ("route", "retrieve", "draft", "total"):
        xs = series[stage]; mean = sum(xs) / len(xs); p = p95(xs)
        flag = "  <- the mean lied" if p > 4 * mean else ""
        print(f"{stage:9} mean= {mean:,.0f}ms  p95= {p:,}ms{flag}")

print("# one live ticket through the cameras:"); one_ticket()
print("# the canned day, digested:"); digest()
