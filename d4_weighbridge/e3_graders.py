# e3_graders.py — mixed methodologies: the grader fits the slice, not the other way round
import json, re

def exact_match(out, expect):                      # refund decision: one right answer -> code
    got = json.loads(out)
    return got["decision"] == expect["decision"] and got.get("amount") == expect.get("amount")

CHECKS = {"apology": r"\b(sorry|apologi[sz]e)", "next_step": r"\b(by|within|before|on)\b"}

def rubric(reply, facts):                          # a checklist a script can tick -> code
    hits = {k: bool(re.search(p, reply, re.I)) for k, p in CHECKS.items()}
    hits["no_invented_date"] = not any(d in reply for d in facts["dates_not_given"])
    return round(sum(hits.values()) / len(hits), 2), hits     # partial credit, itemised

JUDGE = """You grade a Kaveri customer reply for tone and honesty against the rubric.
Reason it through before you decide. End with one word on its own line:
PASS, FAIL or UNKNOWN. Say UNKNOWN if the verdict needs facts you were not shown.
Certainty that the facts below do not support is a FAIL, however fluent.
<rubric>{rubric}</rubric>
<facts>{facts}</facts>
<reply>{reply}</reply>"""

def judge(reply, facts, rubric_text, call):        # judgement -> a calibrated model (E4)
    last = call(JUDGE.format(rubric=rubric_text, facts=facts, reply=reply)).strip().split()[-1]
    return last.upper() if last.upper() in {"PASS", "FAIL", "UNKNOWN"} else "UNKNOWN"

if __name__ == "__main__":                         # DRY_RUN: recorded judge replies, no API
    facts = {"dates_not_given": ["Friday", "tomorrow"]}
    print(exact_match('{"decision": "escalate"}', {"decision": "escalate"}))
    print(rubric("Sorry for the wait - your sofa will reach you by Friday.", facts))
    rec = iter(["...it promises Friday, no carrier date was given.\nFAIL", "...\nMaybe"])
    print(judge("We will deliver by Friday.", facts, "honest dates", lambda p: next(rec)),
          judge("Your claim is with our team.", facts, "honest dates", lambda p: next(rec)))
