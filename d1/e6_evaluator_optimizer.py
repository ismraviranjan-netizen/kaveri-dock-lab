# E6 · Evaluator-optimizer: a writer and an editor, with a page limit  (objective 1.3b, workflow 5)
#
#   Writer (model):  drafts a reply.
#   Editor (model):  checks it against a rubric. Says PASS, or one line of criticism.
#   Writer again:    revises using the criticism. Repeat.
# Two organs: MAX_ROUNDS is the budget, PASS is the exit. E7's agent loop has exactly these two, grown larger.
#
# Run on battery:  DRY_RUN=1 python e6_evaluator_optimizer.py      Run live:  python e6_evaluator_optimizer.py

from common import ask, MODEL_MAIN, EMAIL, DRY_RUN


# ---------------------------------------------------------------
# STEP 0. The budget and the rubric
# ---------------------------------------------------------------

MAX_ROUNDS = 2                            # the budget: the editor gets at most two looks

RUBRIC = (
    "You are an editor at Kaveri Freight. Check the draft below against this rubric:\n"
    "  1. Tone courteous?\n"
    "  2. Facts only, no promises of refunds or compensation?\n"
    "  3. Under 120 words?\n"
    "If all three pass, reply with exactly the single word PASS. "
    "Otherwise reply with ONE line of specific criticism and nothing else.\n\n"
    "Draft:\n"
)


# ---------------------------------------------------------------
# STEP 1. The loop: draft once, then (evaluate, maybe revise) up to MAX_ROUNDS times
# ---------------------------------------------------------------

def draft_and_polish(email_text):

    # 1a. WRITER, first draft. Loose instructions on purpose, so the editor has something to catch.
    draft = ask(MODEL_MAIN, "Reply to this customer exception email on behalf of Kaveri Freight:\n\n" + email_text)
    print("Draft 0:", len(draft.split()), "words")

    # 1b. The editing rounds. range(1, MAX_ROUNDS + 1) is the budget.
    for round_number in range(1, MAX_ROUNDS + 1):

        # EDITOR: PASS, or one line of criticism.
        verdict = ask(MODEL_MAIN, RUBRIC + draft)
        print("Round", round_number, "editor said:", verdict)

        # The exit. PASS means stop early and do not spend the remaining budget.
        if verdict == "PASS":
            break

        # WRITER again: revise using the criticism.
        draft = ask(MODEL_MAIN,
                    "Revise the draft below. Apply this criticism exactly and change nothing else:\n"
                    + verdict + "\n\nDraft:\n" + draft)
        print("Round", round_number, "revised:", len(draft.split()), "words")

    # 1c. Whatever draft we hold now ships: the one that passed, or the best after the budget ran out.
    return draft


if __name__ == "__main__":
    print("# E6 · evaluator-optimizer · " + ("DRY_RUN" if DRY_RUN else "LIVE"))
    final = draft_and_polish(EMAIL)
    print()
    print("=== Final draft ===")
    print(final)
