# E8 · Re-planning — the bridge is out: a finding can change the plan (objective 1.5, dynamic decomposition complete)
# E5's plan, plus a walk-and-look after every finding, plus a second budget: max_new caps how much the plan may grow.
import json
from common import ask_json, MODEL_MAIN, BRIEF, DRY_RUN
from e5_orchestrator_workers import plan_from, run_worker, synthesise     # E5's moves, reused

def replan(brief, max_new=3):                           # cap on growth, too
    tasks = plan_from(brief)                            # E5's opening move
    findings, grew = {}, 0
    next_id = max(t["id"] for t in tasks) + 1
    while tasks:
        sub = tasks.pop(0)
        result = run_worker(sub, findings)              # E5's worker call
        findings[sub["id"]] = result
        print(f"# run {sub['id']}: {sub['task']:<18} -> {result}")
        verdict = ask_json(MODEL_MAIN,                  # the walk-and-look: finding + remaining, not the history
                           "Given this new finding, does the remaining plan still hold? "
                           'Reply {"ok": true} or {"ok": false, "add": ["new subtasks"], "drop": [ids]}\n'
                           + json.dumps({"finding": result, "remaining": tasks}))
        if not verdict.get("ok", True) and grew < max_new:
            drop = set(verdict.get("drop", []))
            tasks = [t for t in tasks if t["id"] not in drop]
            added = verdict.get("add", [])[:max_new - grew]   # never past the cap
            for name in added:                          # the detour appears
                tasks.append({"id": next_id, "task": name, "needs": []}); next_id += 1
            grew += len(added)
            print(f"# replan: ok=false  drop={sorted(drop)}  add={added}")
    print(f"# grew={grew}, budget max_new={max_new} {'EXHAUSTED' if grew >= max_new else 'not exhausted'}")
    return synthesise(brief, findings)                  # E5's closing move

if __name__ == "__main__":
    print(f"# E8 · re-planning · {'DRY_RUN' if DRY_RUN else 'LIVE'}")
    print(replan(BRIEF))
