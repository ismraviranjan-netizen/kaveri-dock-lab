# gen_logday.py — one canned day: 10,000 tickets x 4 stages = 40,000 lines, with a cold-carrier tail
import json, random, uuid
random.seed(214)
TAIL_P = 0.06                                   # 6% of retrievals hit a cold carrier API
with open("logday.jsonl", "w") as f:
    for _ in range(10_000):
        trace = uuid.uuid4().hex[:8]
        route = int(random.gauss(90, 20))
        retrieve = int(random.gauss(250, 60)) + (int(random.gauss(2400, 300)) if random.random() < TAIL_P else 0)
        draft = int(random.gauss(880, 180))
        for stage, ms, tok, pc in (("route", route, 400, 1), ("retrieve", retrieve, 3600, 3), ("draft", draft, 5800, 41)):
            f.write(json.dumps({"trace": trace, "stage": stage, "ms": max(ms, 1), "tokens": tok, "cost_pc": pc}) + "\n")
        f.write(json.dumps({"trace": trace, "stage": "total", "ms": route + retrieve + draft}) + "\n")
print("wrote logday.jsonl, 40,000 lines")
