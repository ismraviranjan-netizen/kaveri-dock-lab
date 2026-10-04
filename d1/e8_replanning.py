# E8 · Re-planning: the bridge is out, a finding can change the plan  (objective 1.5, dynamic decomposition)
#
#   Same three moves as E5 (make_plan -> run_worker -> synthesise), plus after EVERY finding the foreman is asked:
#   "does the remaining plan still make sense?" If not, drop some tasks and add others.
#   A second budget, MAX_NEW, caps how many tasks the plan may grow by. Law 3 applies to plans, not just turns.
#
# Run on battery:  DRY_RUN=1 python e8_replanning.py       Run live:  python e8_replanning.py

import json
from common import ask_json, MODEL_MAIN, BRIEF, DRY_RUN
from e5_orchestrator_workers import make_plan, run_worker, synthesise     # E5's three moves, reused


# ---------------------------------------------------------------
# STEP 0. The growth budget
# ---------------------------------------------------------------

MAX_NEW = 3                               # at most 3 tasks may ever be added to the plan


# ---------------------------------------------------------------
# STEP 1. The new move: after a finding, ask whether the remaining plan still holds.
#         The foreman sees the new finding and the REMAINING tasks, not the whole history.
# ---------------------------------------------------------------

def check_plan(finding, remaining_tasks):
    question = (
        "A worker just reported this finding:\n" + finding + "\n\n"
        "These subtasks are still to be done:\n" + json.dumps(remaining_tasks) + "\n\n"
        "Does the remaining plan still make sense given the finding? Reply with JSON only:\n"
        '  {"ok": true}\n'
        "or\n"
        '  {"ok": false, "drop": [ids of tasks that no longer make sense], "add": ["short name of a new task", ...]}'
    )
    return ask_json(MODEL_MAIN, question)


# ---------------------------------------------------------------
# STEP 2. The loop with re-planning
# ---------------------------------------------------------------

def replan(brief):
    tasks = make_plan(brief)                              # E5's opening move
    print("Initial plan:", json.dumps(tasks))

    findings = {}
    grew = 0                                              # how many tasks have been added so far
    next_id = max(task["id"] for task in tasks) + 1       # fresh ids for added tasks

    while tasks:                                          # keep going until the task list is empty
        current = tasks.pop(0)                            # take the first remaining task
        result = run_worker(current, findings)            # E5's worker call
        findings[current["id"]] = result
        print("Run", current["id"], "(" + current["task"] + ") ->", result)

        verdict = check_plan(result, tasks)               # the walk-and-look

        if verdict.get("ok", True):
            continue                                      # plan still holds, move on

        if grew >= MAX_NEW:
            print("  Replan requested, but the growth budget is spent. Keeping the plan as it is.")
            continue

        # Drop the tasks the foreman says no longer make sense.
        drop_ids = set(verdict.get("drop", []))
        tasks = [task for task in tasks if task["id"] not in drop_ids]

        # Add the new ones as proper task records, but never past the cap.
        room_left = MAX_NEW - grew
        new_names = verdict.get("add", [])[:room_left]
        for name in new_names:
            tasks.append({"id": next_id, "task": name, "needs": []})
            next_id = next_id + 1
        grew = grew + len(new_names)
        print("  REPLAN: dropped", sorted(drop_ids), "added", new_names)

    if grew >= MAX_NEW:
        print("grew=" + str(grew) + ", budget MAX_NEW=" + str(MAX_NEW) + " EXHAUSTED")
    else:
        print("grew=" + str(grew) + ", budget MAX_NEW=" + str(MAX_NEW) + " not exhausted")

    return synthesise(brief, findings)                    # E5's closing move


if __name__ == "__main__":
    print("# E8 · re-planning · " + ("DRY_RUN" if DRY_RUN else "LIVE"))
    print(replan(BRIEF))
