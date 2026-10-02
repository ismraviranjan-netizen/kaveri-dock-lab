# E6 · The retrieval router — three shapes, three machines (objective 3.6)
import os, re
os.environ.setdefault("DRY_RUN", "1")         # the toy foreman is enough for routing
from e4_chunking import by_heading, doc
from e5_hybrid import hybrid

TMS = {"KF-2481": {"status": "CUSTOMS_HOLD", "leg": "ICD Pune"}}      # stub for the TMS
LATE_THIS_WEEK = 41                                                     # stub for the warehouse DB

def structured_lookup(q):
    cid = re.search(r"KF-\d{4}", q).group()
    return TMS[cid]

def sql_aggregate(q):
    return LATE_THIS_WEEK                                               # SELECT count(*) ... WHERE late

def hybrid_rag(q):
    return "answer drafted from " + hybrid(q, by_heading(doc), k=1)[0]

RULES = [                                                               # order matters
    (re.compile(r"KF-\d{4}"),                          structured_lookup),
    (re.compile(r"\bhow many\b|\bcount\b|\btotal\b", re.I), sql_aggregate),
    (re.compile(r".*"),                                hybrid_rag),
]

def route(q):
    for pat, handler in RULES:
        if pat.search(q):
            return handler.__name__, handler(q)

if __name__ == "__main__":
  for q in ("Where is KF-2481 right now?",
            "How many shipments ran late this week?",
            "How do I re-file an e-way bill after a hold?"):
    name, ans = route(q)
    print(f"{name:17} <- {q}\n{'':17} -> {ans}")
