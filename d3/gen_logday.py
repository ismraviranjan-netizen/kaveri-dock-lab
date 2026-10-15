# gen_logday.py  -  one canned day for E7: 10,000 tickets x 4 stages = 40,000 JSON lines, with a cold-carrier tail
#
# Run once:  python gen_logday.py      (writes data/logday.jsonl, about 3 MB; git-ignored)

import json
import random
import uuid
from common import LOGDAY

random.seed(214)
TAIL_P = 0.06                                   # 6% of retrievals hit a cold carrier API


def write(path=LOGDAY, tickets=10_000):
    with open(path, "w") as f:
        for _ in range(tickets):
            trace = uuid.uuid4().hex[:8]
            route = int(random.gauss(90, 20))
            retrieve = int(random.gauss(250, 60))
            if random.random() < TAIL_P:
                retrieve = retrieve + int(random.gauss(2400, 300))
            draft = int(random.gauss(880, 180))
            for stage, ms, tok, pc in (("route", route, 400, 1), ("retrieve", retrieve, 3600, 3), ("draft", draft, 5800, 41)):
                f.write(json.dumps({"trace": trace, "stage": stage, "ms": max(ms, 1), "tokens": tok, "cost_pc": pc}) + "\n")
            f.write(json.dumps({"trace": trace, "stage": "total", "ms": route + retrieve + draft}) + "\n")
    return tickets * 4


if __name__ == "__main__":
    print("wrote " + str(LOGDAY) + ", " + format(write(), ",") + " lines")
