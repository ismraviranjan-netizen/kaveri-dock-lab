# E2 · Permission modes: the same eight actions under six modes
#
#   The CODE computes what each mode does with each action, from the merged rules on the simulated workstation:
#     1. deny rules first, then ask, then allow  (a deny anywhere wins, even over an allow in a "closer" file)
#     2. then the mode: default asks, acceptEdits allows edits, plan only reads, dontAsk denies what is not
#        pre-allowed, auto lets a classifier decide (simulated here), bypassPermissions skips prompts
#   FABLE predicts the whole grid in one call. The code grades it cell by cell.
#
# Run on battery:  DRY_RUN=1 python e2_permission_modes.py   Run live:  python e2_permission_modes.py   (1 call)

import json
import world
from common import ask_schema, served_by, print_bill, MODEL, DRY_RUN

MODES = ["default", "acceptEdits", "plan", "auto", "dontAsk", "bypassPermissions"]
ACTIONS = [  # (action as Claude Code names it, kind, risk the simulated auto classifier assigns)
    ("Read(src/app.py)", "read", "low"),
    ("Read(./.env)", "read", "high"),
    ("Edit(src/app.py)", "edit", "low"),
    ("Bash(npm test)", "bash", "low"),
    ("Bash(git status)", "bash", "low"),
    ("Bash(git push origin main)", "bash", "high"),
    ("Bash(curl https://example.com)", "bash", "high"),
    ("Bash(rm -rf build)", "bash", "high"),
]
OUTCOMES = ["ALLOW", "ASK", "DENY", "BLOCKED", "N/A"]


def decide(mode, action, kind, risk):
    """One cell of the grid. Returns (outcome, reason)."""
    e = world.effective()
    if mode == "bypassPermissions" and e["bypass_disabled"]:
        return "N/A", "disabled by managed settings"
    hit = world.decide_rules(action)
    if hit and hit[0] == "deny":
        return "DENY", "deny " + hit[1] + " (" + hit[2] + ")"
    if mode == "plan":
        return ("ALLOW", "plan mode reads") if kind == "read" else ("BLOCKED", "plan mode: no edits, no commands")
    if kind == "read":
        return "ALLOW", "read-only tools need no approval"
    if hit:
        if hit[0] == "ask":
            return ("DENY", "dontAsk denies anything that would prompt") if mode == "dontAsk" else ("ASK", "ask " + hit[1] + " (" + hit[2] + ")")
        return "ALLOW", "allow " + hit[1] + " (" + hit[2] + ")"
    if mode == "dontAsk":
        return "DENY", "not pre-allowed"
    if mode == "auto":
        return ("ALLOW", "classifier: low risk") if risk == "low" else ("DENY", "classifier: high risk")
    if mode == "acceptEdits" and kind == "edit":
        return "ALLOW", "acceptEdits accepts edits"
    if mode == "bypassPermissions":
        return "ALLOW", "no prompts"
    return "ASK", "no rule: the mode prompts"


SYSTEM = ("You are a Claude Code expert. Predict what Claude Code does with each action in each permission mode, on a "
          "workstation with these merged rules (layer in brackets):\n"
          + "\n".join(k + " " + r + " [" + l + "]" for k, r, l in world.effective()["rules"])
          + "\nManaged settings set disableBypassPermissionsMode. In auto mode assume a classifier allows low-risk "
          "actions and blocks high-risk ones when no rule applies. Outcomes: ALLOW, ASK, DENY, BLOCKED (plan mode refuses "
          "the action), N/A (mode unavailable).")
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["grid"],
          "properties": {"grid": {"type": "array", "items": {
              "type": "object", "additionalProperties": False, "required": ["action", "outcomes"],
              "properties": {"action": {"type": "string"},
                             "outcomes": {"type": "array", "items": {"type": "string", "enum": OUTCOMES}}}}}}}


if __name__ == "__main__":
    e = world.effective()
    print("# E2 · permission modes · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))
    print("  this workstation starts in: " + e["defaultMode"] + "  (from .claude/settings.local.json)")
    print("  rules are checked deny -> ask -> allow; managed paths: " + json.dumps(world.MANAGED_PATHS))

    user = ("Modes, in this column order: " + ", ".join(MODES) + ".\nActions, one grid row each, in this order:\n"
            + "\n".join(a for a, _, _ in ACTIONS) + "\nFor each action give the outcomes list in the mode order above.")
    guess, reply = ask_schema(SYSTEM, user, SCHEMA)
    predicted = {row["action"]: row["outcomes"] for row in guess["grid"]}

    print()
    print("=== THE GRID: the code's answer, with ✓/✗ for Fable's prediction ===" + served_by(reply))
    width = 13
    print("  " + "action".ljust(31) + "".join(("bypass" if m == "bypassPermissions" else m).ljust(width) for m in MODES))
    right, total, misses = 0, 0, []
    for action, kind, risk in ACTIONS:
        row = "  " + action.ljust(31)
        for col, mode in enumerate(MODES):
            truth, reason = decide(mode, action, kind, risk)
            p = predicted.get(action, [None] * len(MODES))
            guess_cell = p[col] if col < len(p) else None
            ok = guess_cell == truth
            right += ok
            total += 1
            if not ok:
                misses.append((action, mode, truth, guess_cell, reason))
            row += (truth + (" ✓" if ok else " ✗")).ljust(width)
        print(row)

    print()
    print("=== WHY, for every cell Fable missed ===" if misses else "=== Fable matched every cell ===")
    for action, mode, truth, g, reason in misses:
        print("  " + action.ljust(31) + mode.ljust(18) + "Fable " + str(g).ljust(8) + "code " + truth.ljust(8) + reason)

    print()
    print("=== WHAT EACH OUTCOME COUNTS TO, PER MODE ===")
    for mode in MODES:
        counts = {o: 0 for o in OUTCOMES}
        for action, kind, risk in ACTIONS:
            counts[decide(mode, action, kind, risk)[0]] += 1
        bar = "".join({"ALLOW": "A", "ASK": "?", "DENY": "x", "BLOCKED": "-", "N/A": "."}[o] * n for o, n in counts.items())
        print("  " + mode.ljust(18) + bar.ljust(10) + "  " + "  ".join(o + " " + str(n) for o, n in counts.items() if n))
    print("  key: A allow · ? ask · x deny · - blocked by plan · . not available")
    print()
    print("  Fable: " + str(right) + " of " + str(total) + " cells. The auto column is a SIMULATED classifier; check the docs for edge cases.")
    print_bill()
