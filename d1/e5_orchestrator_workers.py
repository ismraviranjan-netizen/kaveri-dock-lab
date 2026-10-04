# E5 · Orchestrator-workers: the site foreman writes the plan himself  (objective 1.5, and workflow 4 of 1.3b)
#
#   Foreman (model):   reads the brief, writes a list of subtasks as JSON.
#   Workers (model):   one call per subtask. Each sees ONLY the findings it declared it needs, plus the depot facts.
#   Synthesis (model): sees all findings, writes ONE recommendation.
# The SHAPE (plan -> work -> synthesise) is fixed code. The CONTENT of the plan is the model's.
#
# Run on battery:  DRY_RUN=1 python e5_orchestrator_workers.py      Run live:  python e5_orchestrator_workers.py

import json
from common import ask, ask_json, fake_status, fake_carriers, MODEL_MAIN, MODEL_SMALL, BRIEF, DRY_RUN


# ---------------------------------------------------------------
# STEP 0. The facts the depot system can supply. The CODE hands these to the workers.
#         Workers reason over facts; they do not invent them.
# ---------------------------------------------------------------

FACTS = {
    "shipment": fake_status("KF-2481"),
    "carriers_on_lane": fake_carriers("Pune-Chennai"),
}


# ---------------------------------------------------------------
# STEP 1. FOREMAN: the model writes the plan
# ---------------------------------------------------------------

def make_plan(brief):
    question = (
        "Brief:\n" + brief + "\n\n"
        "Break this into 2 to 5 subtasks. Reply with JSON only, a list like:\n"
        '[{"id": 1, "task": "status check", "needs": []}, {"id": 2, "task": "carrier options", "needs": [1]}]\n'
        '"needs" lists the ids of earlier subtasks whose findings this one depends on.'
    )
    return ask_json(MODEL_MAIN, question)


# ---------------------------------------------------------------
# STEP 2. WORKER: one subtask, on the small model.
#         It is shown ONLY the findings it declared it needs (context isolation), plus the depot facts.
# ---------------------------------------------------------------

def run_worker(subtask, findings_so_far):
    known = {}
    for needed_id in subtask["needs"]:
        if needed_id in findings_so_far:
            known[needed_id] = findings_so_far[needed_id]

    question = (
        "You are a worker at Kaveri Freight. Do this one subtask and reply in one or two lines.\n"
        "Subtask: " + subtask["task"] + "\n"
        "Known findings from earlier subtasks: " + json.dumps(known) + "\n"
        "Depot facts you may use: " + json.dumps(FACTS)
    )
    return ask(MODEL_SMALL, question)


# ---------------------------------------------------------------
# STEP 3. SYNTHESIS: sees everything, writes ONE recommendation
# ---------------------------------------------------------------

def synthesise(brief, findings):
    question = (
        "Brief:\n" + brief + "\n\n"
        "Findings from the workers:\n" + json.dumps(findings, indent=2) + "\n\n"
        "Write ONE recommendation for Meera's desk, three sentences at most, starting with RECOMMENDATION:"
    )
    return ask(MODEL_MAIN, question)


# ---------------------------------------------------------------
# STEP 4. The fixed shape: plan, then work in plan order, then synthesise
# ---------------------------------------------------------------

def orchestrate(brief):
    plan = make_plan(brief)
    print("Foreman's plan:", json.dumps(plan))

    findings = {}
    for subtask in plan:                                   # the plan executes in order once written
        result = run_worker(subtask, findings)
        findings[subtask["id"]] = result
        print("Worker", subtask["id"], "(" + subtask["task"] + ") needs", subtask["needs"], "->", result)

    return synthesise(brief, findings)


if __name__ == "__main__":
    print("# E5 · orchestrator-workers · " + ("DRY_RUN" if DRY_RUN else "LIVE"))
    print(orchestrate(BRIEF))
