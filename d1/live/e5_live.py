# e5_live.py
# E5: orchestrator-workers. The site foreman writes the plan himself.
#   Foreman (model):   reads the brief, writes a list of subtasks as JSON.
#   Workers (model):   one call per subtask. Each sees only the findings it declared it needs.
#   Synthesis (model): sees all findings, writes ONE recommendation.
# The SHAPE (plan -> work -> synthesise) is fixed code. The CONTENT of the plan is the model's.
#
# Before running:   pip install anthropic   and   ANTHROPIC_API_KEY in the environment
# Run:              python e5_live.py

import json
import anthropic


# ---------------------------------------------------------------
# STEP 0. Things we decide before talking to the model
# ---------------------------------------------------------------

MODEL_FOREMAN = "claude-sonnet-5-5"   # planning and synthesis need judgement
MODEL_WORKER = "claude-haiku-4-5"     # each subtask is small and focused
MAX_TOKENS = 1024

BRIEF = """KF-2481's customer (Padma Deshmukh) is threatening to leave. The consignment is three days late on the Pune-Chennai lane. Find out why it is stuck and recommend what Meera's desk should do today."""


# ---------------------------------------------------------------
# STEP 1. Connect, and two helpers: ask for text, and ask for JSON.
# ---------------------------------------------------------------

client = anthropic.Anthropic()

def ask(model, question):
    reply = client.messages.create(
        model=model,
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

def ask_json(model, question):
    raw = ask(model, question)

    # Models sometimes wrap JSON in a ```json ... ``` fence. Strip it if present.
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:]                 # drop the opening ```json line
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]            # drop the closing ``` line
        raw = "\n".join(lines)

    return json.loads(raw)


# ---------------------------------------------------------------
# STEP 2. The foreman writes the plan.
# ---------------------------------------------------------------

def make_plan(brief):
    question = (
        "Brief:\n" + brief + "\n\n"
        "Break this into 2 to 5 subtasks. Reply with JSON only, a list like:\n"
        '[{"id": 1, "task": "status check", "needs": []}, {"id": 2, "task": "carrier options", "needs": [1]}]\n'
        '"needs" lists the ids of earlier subtasks whose findings this one depends on.'
    )
    return ask_json(MODEL_FOREMAN, question)


# ---------------------------------------------------------------
# STEP 3. One worker does one subtask. It is shown ONLY the findings it declared it needs.
# ---------------------------------------------------------------

def run_worker(subtask, findings_so_far):
    # Collect just the findings this subtask asked for.
    known = {}
    for needed_id in subtask["needs"]:
        if needed_id in findings_so_far:
            known[needed_id] = findings_so_far[needed_id]

    question = (
        "You are a worker at Kaveri Freight. Do this one subtask and reply in one or two lines.\n"
        "Subtask: " + subtask["task"] + "\n"
        "Known facts from earlier subtasks: " + json.dumps(known) + "\n"
        "Context: consignment KF-2481, Pune-Chennai, three days late. "
        "If you have no data, state the most likely finding for a late Indian domestic consignment."
    )
    return ask(MODEL_WORKER, question)


# ---------------------------------------------------------------
# STEP 4. Synthesis sees everything and writes one recommendation.
# ---------------------------------------------------------------

def synthesise(brief, findings):
    question = (
        "Brief:\n" + brief + "\n\n"
        "Findings from the workers:\n" + json.dumps(findings, indent=2) + "\n\n"
        "Write ONE recommendation for Meera's desk, three sentences at most, starting with RECOMMENDATION:"
    )
    return ask(MODEL_FOREMAN, question)


# ---------------------------------------------------------------
# STEP 5. Run the three stages in the fixed order.
# ---------------------------------------------------------------

print("=== Foreman writes the plan ===")
plan = make_plan(BRIEF)
print(json.dumps(plan, indent=2))

print()
print("=== Workers run, one per subtask, in plan order ===")
findings = {}
for subtask in plan:
    result = run_worker(subtask, findings)
    findings[subtask["id"]] = result
    print("Worker", subtask["id"], "(" + subtask["task"] + ") needs", subtask["needs"], "->", result)

print()
print("=== Synthesis ===")
print(synthesise(BRIEF, findings))
