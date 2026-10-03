# e6_live.py
# E6: evaluator-optimizer. A writer and an editor, with a page limit.
#   Writer (model):  drafts a reply.
#   Editor (model):  checks it against a rubric. Says PASS, or one line of criticism.
#   Writer again:    revises using the criticism. Repeat.
# Two safety organs: max_rounds (the budget) and PASS (the exit). E7's agent loop has exactly these two, grown larger.
#
# Before running:   pip install anthropic   and   ANTHROPIC_API_KEY in the environment
# Run:              python e6_live.py

import anthropic


# ---------------------------------------------------------------
# STEP 0. Things we decide before talking to the model
# ---------------------------------------------------------------

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 1024
MAX_ROUNDS = 2                    # the budget: the editor gets at most two looks

EMAIL = """Subject: KF-2481 - where is my shipment?? Three days late!

Hello Kaveri,

My consignment KF-2481 (Pune to Chennai, 12 cartons of textile samples) was promised on Monday. It is now Thursday. Your portal says "in transit" and nothing else. My buyer is threatening to cancel the order.

Where is it right now, and what are you doing about it?

- Padma Deshmukh
"""

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
# STEP 1. Connect, and the helper.
# ---------------------------------------------------------------

client = anthropic.Anthropic()

def ask(question):
    reply = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": question}],
    )
    if reply.stop_reason == "refusal":
        raise RuntimeError("The model declined to answer.")
    answer = ""
    for block in reply.content:
        if block.type == "text":
            answer = answer + block.text
    return answer.strip()


# ---------------------------------------------------------------
# STEP 2. The loop: draft, then (evaluate, maybe revise) up to MAX_ROUNDS times.
# ---------------------------------------------------------------

def draft_and_polish(email_text):
    # 2a. First draft. Deliberately loose instructions so the editor has something to catch.
    draft = ask("Reply to this customer exception email on behalf of Kaveri Freight:\n\n" + email_text)
    print("Draft 0:", len(draft.split()), "words")

    # 2b. The editing rounds. range(MAX_ROUNDS) is the budget.
    for round_number in range(1, MAX_ROUNDS + 1):
        verdict = ask(RUBRIC + draft)
        print("Round", round_number, "editor said:", verdict)

        # The exit. PASS means stop early, do not spend the remaining budget.
        if verdict == "PASS":
            break

        # Not PASS: revise using the criticism.
        draft = ask(
            "Revise the draft below. Apply this criticism exactly and change nothing else:\n"
            + verdict + "\n\nDraft:\n" + draft
        )
        print("Round", round_number, "revised:", len(draft.split()), "words")

    return draft


# ---------------------------------------------------------------
# STEP 3. Run it.
# ---------------------------------------------------------------

final = draft_and_polish(EMAIL)
print()
print("=== Final draft ===")
print(final)
