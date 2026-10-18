# E5 · Orchestrator-workers: the site foreman writes the plan himself  (objective 1.5, and workflow 4 of 1.3b)
#
#   Foreman (model):   reads the brief, writes a list of subtasks as JSON.
#   Workers (model):   one call per subtask. Each sees ONLY the findings it declared it needs, plus the depot facts.
#   Synthesis (model): sees all findings, writes ONE recommendation.
# The SHAPE (plan -> work -> synthesise) is fixed code. The CONTENT of the plan is the model's.
#
# Run on battery:  DRY_RUN=1 python e5_orchestrator_workers.py      Run live:  python e5_orchestrator_workers.py

import json
import textwrap
from common import ask, ask_json, fake_status, fake_carriers, MODEL, BRIEF, DRY_RUN

WIDTH = 100                                            # wrap long model text so the terminal stays readable


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
    return ask_json(MODEL, question)


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
    return ask(MODEL, question)


# ---------------------------------------------------------------
# STEP 3. SYNTHESIS: sees everything, writes ONE recommendation
# ---------------------------------------------------------------

def synthesise(brief, findings):
    question = (
        "Brief:\n" + brief + "\n\n"
        "Findings from the workers:\n" + json.dumps(findings, indent=2) + "\n\n"
        "Write ONE recommendation for Meera's desk, three sentences at most, starting with RECOMMENDATION:"
    )
    return ask(MODEL, question)


# ---------------------------------------------------------------
# STEP 4. Printing helpers. Nothing here touches the model: they only lay the output out.
# ---------------------------------------------------------------

def heading(text):
    print()
    print("=== " + text + " ===")


def block(label, text, indent="    "):
    """A label on its own line, then the text wrapped underneath it."""
    print(label)
    for paragraph in text.strip().split("\n"):
        print(textwrap.fill(paragraph, WIDTH, initial_indent=indent, subsequent_indent=indent) if paragraph.strip() else "")


def show_plan(plan):
    """The foreman's plan as a table: id, what it waits for, the task."""
    print("  id  needs   task")
    for subtask in plan:
        needs = ",".join(str(n) for n in subtask["needs"]) or "-"
        first, *rest = textwrap.wrap(subtask["task"], WIDTH - 14) or [""]
        print("  " + str(subtask["id"]).ljust(4) + needs.ljust(8) + first)
        for line in rest:
            print(" " * 14 + line)


# ---------------------------------------------------------------
# STEP 5. The fixed shape: plan, then work in plan order, then synthesise
# ---------------------------------------------------------------

def orchestrate(brief):
    heading("FOREMAN · the model writes the plan (1 call)")
    plan = make_plan(brief)
    show_plan(plan)

    heading("WORKERS · one call per subtask, each sees only the findings it asked for")
    findings = {}
    for subtask in plan:                                   # the plan executes in order once written
        result = run_worker(subtask, findings)
        findings[subtask["id"]] = result
        print()
        block("Worker " + str(subtask["id"]) + " · needs " + (str(subtask["needs"]) if subtask["needs"] else "nothing")
              + " · " + textwrap.shorten(subtask["task"], 70), result)

    heading("SYNTHESIS · sees every finding, writes one recommendation (1 call)")
    recommendation = synthesise(brief, findings)
    block("", recommendation, indent="  ")
    print()
    print("Calls made: 1 plan + " + str(len(plan)) + " workers + 1 synthesis = " + str(len(plan) + 2))
    return recommendation


if __name__ == "__main__":
    print("# E5 · orchestrator-workers · " + ("DRY_RUN" if DRY_RUN else "LIVE"))
    orchestrate(BRIEF)
