# E8 · Re-planning: the bridge is out, a finding can change the plan  (objective 1.5, dynamic decomposition)
#
#   Same three moves as E5 (make_plan -> run_worker -> synthesise), plus after EVERY finding the foreman is asked:
#   "does the remaining plan still make sense?" If not, drop some tasks and add others.
#   A second budget, MAX_NEW, caps how many tasks the plan may grow by. Law 3 applies to plans, not just turns.
#   A second guard, UNAVAILABLE: a finding that says "the data is not here" is a dead end, not a reason to replan.
#   Without it (seen live with MAX_NEW=30) one missing fact spawned a six-task lineage of rephrased fetches.
#
#   The output is laid out so the plan can be WATCHED changing: the plan as a table at the start, one block per
#   run (the task, what it needed, the finding, the foreman's verdict), the remaining plan reprinted after every
#   replan with a growth meter, and a ledger at the end of what was planned, run, dropped and added.
#
# Run on battery:  DRY_RUN=1 python e8_replanning.py       Run live:  python e8_replanning.py

import json
import re
import textwrap
from common import ask_json, MODEL, BRIEF, DRY_RUN
from e5_orchestrator_workers import make_plan, run_worker, synthesise     # E5's three moves, reused
from e5_orchestrator_workers import heading, block, show_plan              # E5's printing helpers, reused


# ---------------------------------------------------------------
# STEP 0. The growth budget
# ---------------------------------------------------------------

MAX_NEW = 3                               # at most 3 tasks may ever be added to the plan

# The second guard, learned from the MAX_NEW=30 run: when a worker reports that the data it needed is simply not
# there, asking the foreman "does the plan still hold?" only produces another fetch task for the same missing data.
# A finding that says "unavailable" is terminal. The CODE decides that; the foreman is not asked.
UNAVAILABLE = re.compile(
    r"not (?:in|available|recorded|included)|isn't (?:in|confirmed)|aren't in|unavailable"
    r"|\bno (?:\w+[ /-])*(?:record|data|access)\b|don't have (?:\w+[ /-])*access"
    r"|\bblocked\b(?::| pending| until)|cannot (?:be )?(?:confirm|pull|retrieve|complete|generate|access|re-attempt)"
    r"|can't (?:confirm|pull|retrieve|complete|generate|access|send)",
    re.IGNORECASE)


def data_unavailable(finding):
    """True when the worker's finding says the facts it needed do not exist here. Plain pattern match, no model."""
    return UNAVAILABLE.search(finding) is not None


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
    return ask_json(MODEL, question)


# ---------------------------------------------------------------
# STEP 2. Printing helpers specific to re-planning. They only print.
# ---------------------------------------------------------------

def growth_meter(grew):
    """grew 2 of 3  [##.]"""
    return "grew " + str(grew) + " of " + str(MAX_NEW) + "  [" + "#" * grew + "." * (MAX_NEW - grew) + "]"


def show_remaining(tasks, grew):
    if tasks:
        print("    remaining plan (" + str(len(tasks)) + " task" + ("" if len(tasks) == 1 else "s") + ") · " + growth_meter(grew))
        show_plan(tasks)
    else:
        print("    remaining plan: empty · " + growth_meter(grew))


def ledger(initial, order, dropped, added, grew, checks):
    heading("LEDGER · what was planned, what actually ran")
    print("  initial plan      : " + ", ".join(str(t["id"]) for t in initial) + "   (" + str(len(initial)) + " tasks from the foreman)")
    print("  ran, in order     : " + ", ".join(str(i) for i in order) + "   (" + str(len(order)) + " worker calls)")
    print("  dropped unrun     : " + (", ".join(str(i) for i in dropped) if dropped else "none"))
    print("  added on the way  : " + (", ".join(str(t["id"]) + " " + repr(t["task"]) for t in added) if added else "none"))
    print("  growth budget     : " + growth_meter(grew) + ("  EXHAUSTED" if grew >= MAX_NEW else "  not exhausted"))
    print("  plan checks       : " + str(checks["asked"]) + " asked · " + str(checks["ok"]) + " said OK · "
          + str(checks["replan"]) + " replanned · " + str(checks["blocked"]) + " blocked by the budget · "
          + str(checks["skipped"]) + " skipped (data unavailable, nothing to replan on)")
    print("  calls made        : 1 plan + " + str(len(order)) + " workers + " + str(checks["asked"]) + " checks + 1 synthesis = "
          + str(2 + len(order) + checks["asked"]))


# ---------------------------------------------------------------
# STEP 3. The loop with re-planning. Identical in logic to the plain version; the prints are the only addition.
# ---------------------------------------------------------------

def replan(brief):
    heading("FOREMAN · the initial plan (1 call)")
    tasks = make_plan(brief)                              # E5's opening move
    initial = list(tasks)
    show_plan(tasks)

    findings = {}
    grew = 0                                              # how many tasks have been added so far
    next_id = max(task["id"] for task in tasks) + 1       # fresh ids for added tasks
    order, dropped, added = [], [], []                    # for the ledger only
    checks = {"asked": 0, "ok": 0, "replan": 0, "blocked": 0, "skipped": 0}

    heading("WORK · one worker per task, then 'does the rest of the plan still hold?' after EVERY finding")
    run_number = 0
    while tasks:                                          # keep going until the task list is empty
        current = tasks.pop(0)                            # take the first remaining task
        run_number = run_number + 1
        result = run_worker(current, findings)            # E5's worker call
        findings[current["id"]] = result
        order.append(current["id"])
        print()
        block("Run " + str(run_number) + " · task " + str(current["id"]) + " · needs "
              + (str(current["needs"]) if current["needs"] else "nothing") + " · " + textwrap.shorten(current["task"], 70), result)

        if data_unavailable(result):                      # the second guard: a dead end is not a reason to replan
            checks["skipped"] = checks["skipped"] + 1
            print("    foreman NOT asked: the worker says the data is unavailable here. Replanning would only add "
                  "another fetch for the same missing data · " + str(len(tasks)) + " task"
                  + ("" if len(tasks) == 1 else "s") + " left · " + growth_meter(grew))
            continue

        verdict = check_plan(result, tasks)               # the walk-and-look
        checks["asked"] = checks["asked"] + 1

        if verdict.get("ok", True):
            checks["ok"] = checks["ok"] + 1
            print("    foreman: plan still holds · " + str(len(tasks)) + " task" + ("" if len(tasks) == 1 else "s") + " left · " + growth_meter(grew))
            continue                                      # plan still holds, move on

        if grew >= MAX_NEW:
            checks["blocked"] = checks["blocked"] + 1
            print("    foreman: wants to replan (drop " + str(verdict.get("drop", [])) + ", add " + str(verdict.get("add", []))
                  + ") · BLOCKED: the growth budget is spent · " + growth_meter(grew))
            continue

        # Drop the tasks the foreman says no longer make sense.
        drop_ids = set(verdict.get("drop", []))
        dropped.extend(task["id"] for task in tasks if task["id"] in drop_ids)
        tasks = [task for task in tasks if task["id"] not in drop_ids]

        # Add the new ones as proper task records, but never past the cap.
        room_left = MAX_NEW - grew
        new_names = verdict.get("add", [])[:room_left]
        cut = len(verdict.get("add", [])) - len(new_names)
        for name in new_names:
            tasks.append({"id": next_id, "task": name, "needs": []})
            added.append(tasks[-1])
            next_id = next_id + 1
        grew = grew + len(new_names)
        checks["replan"] = checks["replan"] + 1
        print("    foreman: REPLAN · dropped " + str(sorted(drop_ids)) + " · added " + str(new_names)
              + ("  (" + str(cut) + " more suggested, cut by the budget)" if cut else ""))
        show_remaining(tasks, grew)

    ledger(initial, order, dropped, added, grew, checks)

    heading("SYNTHESIS · sees every finding, writes one recommendation (1 call)")
    recommendation = synthesise(brief, findings)          # E5's closing move
    block("", recommendation, indent="  ")
    return recommendation


if __name__ == "__main__":
    print("# E8 · re-planning · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL) + " · MAX_NEW=" + str(MAX_NEW))
    replan(BRIEF)
