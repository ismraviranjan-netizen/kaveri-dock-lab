# E3 · Effort and thinking: turn the dial first  (objectives 2.1, 2.3)
#
#   Same prompt three times; only the effort dial changes. Thinking is billed as OUTPUT, so the dial is a
#   cost lever as much as a quality lever. Then a probe: on Fable a manual thinking budget is refused with a 400,
#   because thinking is adaptive and always on. A 400 is not billed.
#   The grader is you: keep the lowest effort whose answer still meets your bar, before you touch the prompt.
#
# Run on battery:  DRY_RUN=1 python e3_effort_dial.py        Run live:  python e3_effort_dial.py

import time
from common import make_client, create_message, text_of, thinking_tokens, cost_inr, served_by, BadRequestError, MODEL, DRY_RUN

SYSTEM = "You are the Kaveri Desk assistant. Reply in at most three sentences."
ASK = [{"role": "user", "content": "KF-2481 is held at customs with an e-way bill mismatch. "
                                   "What should the dispatcher do in the next hour?"}]


if __name__ == "__main__":
    print("# E3 · effort dial · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))

    # STEP 1. The same question at three efforts. One row per call.
    print()
    print("=== same prompt, three settings of the dial ===")
    print("  " + "effort".ljust(8) + "output".rjust(8) + "thinking".rjust(10) + "secs".rjust(7) + "Rs/call".rjust(9))
    for effort in ("high", "medium", "low"):
        started = time.perf_counter()
        reply = create_message(model=MODEL, max_tokens=8000, system=SYSTEM, messages=ASK, output_config={"effort": effort})
        secs = time.perf_counter() - started
        u = reply.usage
        print("  " + effort.ljust(8) + format(u.output_tokens, ",").rjust(8) + format(thinking_tokens(u), ",").rjust(10)
              + format(secs, ".1f").rjust(7) + format(cost_inr(u), ".3f").rjust(9) + served_by(reply))
        print("      " + text_of(reply)[:120].replace("\n", " "))

    # STEP 2. The probe: a manual budget on an adaptive-thinking model. Expect HTTP 400, unbilled.
    print()
    print("=== probe: thinking={'type': 'enabled', 'budget_tokens': 1024} ===")
    try:
        make_client().messages.create(model=MODEL, max_tokens=4096, messages=ASK,
                                      thinking={"type": "enabled", "budget_tokens": 1024})
        print("  budget_tokens accepted - check the thinking docs again")
    except BadRequestError as error:                   # a 400 is not billed
        print("  budget_tokens on " + MODEL + ": HTTP " + str(getattr(error, "status_code", 400)) + " (refused, not billed)")

    print()
    print("effort is a signal, not a cap. You are the grader: keep the lowest effort whose answer")
    print("still meets your bar, before you touch the prompt.")
