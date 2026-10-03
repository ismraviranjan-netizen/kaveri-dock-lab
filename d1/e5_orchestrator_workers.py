# E5 · Orchestrator-workers — the site foreman writes the plan himself (objective 1.5, and workflow 4 of 1.3b)
# The structure (delegate -> work -> synthesise) is fixed code. The content of the plan is the model's.
import json
from common import ask, ask_json, MODEL_MAIN, MODEL_SMALL, BRIEF, DRY_RUN

def plan_from(brief):                                   # the model WRITES the plan
    return ask_json(MODEL_MAIN, "Brief:\n" + brief + "\nList 2-5 subtasks as JSON: "
                                '[{"id": 1, "task": "...", "needs": []}, ...]')

def run_worker(sub, findings):                          # code STEERS: a worker sees only its declared needs
    deps = {i: findings[i] for i in sub["needs"] if i in findings}
    return ask(MODEL_SMALL, f"Subtask: {sub['task']}\nKnown: {json.dumps(deps)}")

def synthesise(brief, findings):                        # synthesis sees everything, writes ONE recommendation
    return ask(MODEL_MAIN, "Brief:\n" + brief + "\nFindings:\n" + json.dumps(findings)
                           + "\nSynthesise one recommendation for Meera.")

def orchestrate(brief):
    plan = plan_from(brief)
    print("# foreman's plan:", json.dumps(plan))
    findings = {}
    for sub in plan:                                    # the plan executes fixedly once written
        findings[sub["id"]] = run_worker(sub, findings)
        print(f"# worker {sub['id']} {sub['task']:<16} needs={sub['needs']} -> {findings[sub['id']]}")
    return synthesise(brief, findings)

if __name__ == "__main__":
    print(f"# E5 · orchestrator-workers · {'DRY_RUN' if DRY_RUN else 'LIVE'}")
    print(orchestrate(BRIEF))
