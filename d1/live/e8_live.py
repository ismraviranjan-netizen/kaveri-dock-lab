# e8_live.py
# E8: re-planning. The bridge is out: a finding can change the plan.
#   Same three stages as E5 (plan -> work -> synthesise), plus after EVERY finding the foreman is asked:
#   "does the remaining plan still hold?" If not, drop some tasks and add others.
#   A second budget, MAX_NEW, caps how many tasks the plan may grow by.
#
# Before running:   pip install anthropic   and   ANTHROPIC_API_KEY in the environment
# Run:              python e8_live.py

import json
import anthropic


# ---------------------------------------------------------------
# STEP 0. Things we decide before talking to the model
# ---------------------------------------------------------------

MODEL_FOREMAN = "claude-sonnet-5-5"
MODEL_WORKER = "claude-haiku-4-5"
MAX_TOKENS = 1024
MAX_NEW = 3                       # the growth budget: at most 3 tasks may be added, ever

BRIEF = """KF-2481's customer (Padma Deshmukh) is threatening to leave. The consignment is three days late on the Pune-Chennai lane. Find out why it is stuck and recommend what Meera's desk should do today."""


# ---------------------------------------------------------------
# STEP 1. Connect, and the two helpers (same as E5).
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
    if raw.startswith("```"):
        lines = raw.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return json.loads(raw)


# ---------------------------------------------------------------
# STEP 2. The three E5 moves, unchanged.
# ---------------------------------------------------------------

def make_plan(brief):
    question = (
        "Brief:\n" + brief + "\n\n"
        "Break this into 2 to 5 subtasks. Reply with JSON only, a list like:\n"
        '[{"id": 1, "task": "status check", "needs": []}, {"id": 2, "task": "carrier options", "needs": [1]}]'
    )
    return ask_json(MODEL_FOREMAN, question)

def run_worker(subtask, findings_so_far):
    known = {}
    for needed_id in subtask["needs"]:
        if needed_id in findings_so_far:
            known[needed_id] = findings_so_far[needed_id]
    question = (
        "You are a worker at Kaveri Freight. Do this one subtask and reply in one or two lines.\n"
        "Subtask: " + subtask["task"] + "\n"
        "Known facts from earlier subtasks: " + json.dumps(known) + "\n"
        "Context: consignment KF-2481, Pune-Chennai, three days late. "
        "If asked for status, report: CUSTOMS_HOLD at Chennai depot, missing e-way bill. "
        "Otherwise state the most likely finding."
    )
    return ask(MODEL_WORKER, question)

def synthesise(brief, findings):
    question = (
        "Brief:\n" + brief + "\n\nFindings:\n" + json.dumps(findings, indent=2)
        + "\n\nWrite ONE recommendation for Meera's desk, three sentences at most, starting with RECOMMENDATION:"
    )
    return ask(MODEL_FOREMAN, question)


# ---------------------------------------------------------------
# STEP 3. The new move: after a finding, ask whether the remaining plan still holds.
#         The foreman sees the new finding and the REMAINING tasks, not the whole history.
# ---------------------------------------------------------------

def check_plan(finding, remaining_tasks):
    question = (
        "A worker just reported this finding:\n" + finding + "\n\n"
        "These subtasks are still to be done:\n" + json.dumps(remaining_tasks) + "\n\n"
        "Does the remaining plan still make sense given the finding? Reply with JSON only:\n"
        '  {"ok": true}\n'
        'or\n'
        '  {"ok": false, "drop": [ids of tasks that no longer make sense], "add": ["short name of a new task", ...]}'
    )
    return ask_json(MODEL_FOREMAN, question)


# ---------------------------------------------------------------
# STEP 4. The loop with re-planning.
# ---------------------------------------------------------------

def replan(brief):
    tasks = make_plan(brief)
    print("Initial plan:", json.dumps(tasks))
    print()

    findings = {}
    tasks_added = 0
    next_id = max(task["id"] for task in tasks) + 1

    while tasks:                                        # keep going until the task list is empty
        current = tasks.pop(0)                          # take the first remaining task
        result = run_worker(current, findings)
        findings[current["id"]] = result
        print("Run", current["id"], "(" + current["task"] + ") ->", result)

        verdict = check_plan(result, tasks)

        if verdict.get("ok", True):
            continue                                    # plan still holds, move on

        if tasks_added >= MAX_NEW:
            print("  Replan requested, but the growth budget is spent. Keeping the plan as is.")
            continue

        # Drop the tasks the foreman says no longer make sense.
        drop_ids = set(verdict.get("drop", []))
        tasks = [task for task in tasks if task["id"] not in drop_ids]

        # Add the new ones, but never past the cap.
        room_left = MAX_NEW - tasks_added
        new_names = verdict.get("add", [])[:room_left]
        for name in new_names:
            tasks.append({"id": next_id, "task": name, "needs": []})
            next_id = next_id + 1
        tasks_added = tasks_added + len(new_names)

        print("  REPLAN: dropped", sorted(drop_ids), "added", new_names)

    print()
    print("Tasks added in total:", tasks_added, "of a budget of", MAX_NEW)
    return synthesise(brief, findings)


# ---------------------------------------------------------------
# STEP 5. Run it.
# ---------------------------------------------------------------

print("=== Re-planning run ===")
print()
print(replan(BRIEF))
