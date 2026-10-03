# E6 · Evaluator-optimizer — the writer and the editor, with a page limit (objective 1.3b, workflow 5)
# Two organs: max_rounds (the budget) and PASS (the exit). E7's agent loop needs exactly these two, grown larger.
from common import ask, MODEL_MAIN, EMAIL, DRY_RUN

RUBRIC = "Rubric: tone courteous? facts only? under 120 words? Reply PASS, or one line of specific criticism:\n"

def draft_and_polish(email, max_rounds=2):
    draft = ask(MODEL_MAIN, "Reply to this exception email:\n" + email)
    print(f"# draft 0: {len(draft.split())} words")
    for round_no in range(max_rounds):                  # the budget
        verdict = ask(MODEL_MAIN, RUBRIC + draft)
        print(f"# round {round_no + 1} editor -> {verdict}")
        if verdict.strip() == "PASS":                   # the exit
            break
        draft = ask(MODEL_MAIN, f"Revise. Criticism: {verdict}\nDraft:\n{draft}")
        print(f"# round {round_no + 1} revised: {len(draft.split())} words")
    return draft

if __name__ == "__main__":
    print(f"# E6 · evaluator-optimizer · {'DRY_RUN' if DRY_RUN else 'LIVE'}")
    print(draft_and_polish(EMAIL))
