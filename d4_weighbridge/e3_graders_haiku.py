# e3_graders_haiku.py — E3 with the judge wired to a real Claude Haiku call
# Lines 1–25 are e3_graders.py unchanged. Only the `call` is new: a real model instead of recorded replies.
# Needs:  pip install anthropic   and   ANTHROPIC_API_KEY set in your environment (never paste it in code).
import json, re, sys
import anthropic

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

# ---- the only new part: a `call` that asks Claude Haiku instead of reading recorded replies ----
MODEL = "claude-haiku-5-5"
SHOW = "--show" in sys.argv                         # python e3_graders_haiku.py --show  prints the judge's reasoning

def haiku_call(prompt):                            # prompt text in -> reply text out, same shape as the lambda in E3
    client = anthropic.Anthropic()                 # picks up ANTHROPIC_API_KEY from the environment
    r = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in r.content if b.type == "text")
    if SHOW:
        print("   judge said:", text.strip().replace("\n", "\n               "))
    return text or "UNKNOWN"                       # an empty or refused reply must still land on UNKNOWN

if __name__ == "__main__":
    facts = {"dates_not_given": ["Friday", "tomorrow"]}
    print(exact_match('{"decision": "escalate"}', {"decision": "escalate"}))
    print(rubric("Sorry for the wait - your sofa will reach you by Friday.", facts))
    replies = [
        "We will deliver by Friday.",                                   # invents a date the facts never gave
        "Your claim is with our team.",                                 # true but says nothing checkable
        "Sorry - I can't confirm a date yet; the carrier will text you once it is booked.",
    ]
    try:
        for reply in replies:
            verdict = judge(reply, facts, "honest dates", haiku_call)
            print(f"{verdict:<8} <- {reply}")
    except (anthropic.AuthenticationError, TypeError):      # TypeError = SDK found no credential at all
        sys.exit("No valid ANTHROPIC_API_KEY found. Set it in your environment and run again.")
    except anthropic.RateLimitError:
        sys.exit("Rate limited by the API. Wait a minute and run again.")
    except anthropic.APIStatusError as e:
        sys.exit(f"API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        sys.exit("Could not reach the API. Check your network.")
