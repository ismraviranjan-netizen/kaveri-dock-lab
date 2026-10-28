# E1 · The debug ladder (7.3): from cheap to heavy
#
#   Seven tickets from Arjun's laptop. For each one:
#     1. FABLE, the student, reads only the symptom and the ladder table and names the ONE command to run first.
#     2. The CODE climbs the ladder on the simulated workstation, rung by rung, and stops at the first rung whose
#        output actually shows the cause. That rung is the right answer: the cheapest one that answers.
#     3. The code grades Fable. Soft judgement from the model, hard grading from the code.
#
# Run on battery:  DRY_RUN=1 python e1_debug_ladder.py      Run live:  python e1_debug_ladder.py   (7 calls, effort low)

import textwrap
import world
from common import ask_schema, served_by, print_bill, MODEL, DRY_RUN

TICKETS = [  # (symptom as the developer reports it, the words that identify the cause in a rung's output)
    ("The API bill went to my personal key, not the Kaveri team workspace.", "personal key"),
    ("I wrote a hook that should run before every Write, and it never fires.", "hooks.json"),
    ("Claude says the tool mcp__carrier-portal__get_eta does not exist.", "carrier-portal"),
    ("I allowed curl in my settings.local.json and every curl is still blocked.", "wins: deny"),
    ("Claude keeps ignoring the SOP 214 rules we wrote in docs/CLAUDE.md.", "docs/CLAUDE.md"),
    ("The changelog says the feature shipped, auto-update says done, and I still don't have it.", "two installs"),
    ("npm test is blocked by our guard hook sometimes, with no message at all.", "timed out"),
]

SYSTEM = ("You are a Claude Code expert helping a developer debug their setup. The debug ladder, cheapest first:\n"
          + "\n".join(str(i + 1) + ". " + cmd + " - " + q for i, (cmd, _, q) in enumerate(world.LADDER))
          + "\nPick the ONE command the developer should run FIRST: the cheapest rung that will show the cause.")
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["command", "why"],
          "properties": {"command": {"type": "string", "enum": [cmd for cmd, _, _ in world.LADDER]},
                         "why": {"type": "string"}}}


def climb(clue):
    """Run the rungs in order; return (index, command, output, matching lines) for the first rung that shows the clue."""
    for index, (cmd, fn, _) in enumerate(world.LADDER):
        lines = fn()
        hits = [line for line in lines if clue in line]
        if hits:
            return index, cmd, lines, hits
    return None


if __name__ == "__main__":
    print("# E1 · debug ladder · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL) + " · " + str(len(TICKETS)) + " tickets")
    print()
    print("=== THE LADDER, cheap to heavy (lines of output on this workstation) ===")
    for i, (cmd, fn, q) in enumerate(world.LADDER, 1):
        print("  " + str(i) + "  " + cmd.ljust(13) + ("█" * min(len(fn()), 36)).ljust(37) + str(len(fn())).rjust(3) + "  " + q)

    score, rungs_used = 0, []
    for n, (symptom, clue) in enumerate(TICKETS, 1):
        print()
        print("--- ticket " + str(n) + " " + "-" * 80)
        print("  symptom : " + symptom)
        guess, reply = ask_schema(SYSTEM, "Symptom: " + symptom, SCHEMA)
        index, cmd, lines, hits = climb(clue)
        rungs_used.append(index + 1)
        ok = guess["command"] == cmd
        score += ok
        print("  Fable   : " + guess["command"].ljust(13) + textwrap.shorten(guess["why"], 95) + served_by(reply))
        print("  climbed : " + " -> ".join(c for c, _, _ in world.LADDER[:index]) + ("  (no sign of it)  -> " if index else "") + cmd + "  ANSWERS")
        print("  output of " + cmd + ":")
        for line in lines[:12]:
            print("     " + ("» " if line in hits else "  ") + line)
        print("  grade   : " + ("✓ cheapest rung" if ok else "✗ the cheapest rung that answers is " + cmd))

    print()
    print("=== SCORECARD ===")
    print("  Fable picked the cheapest answering rung on " + str(score) + " of " + str(len(TICKETS)) + " tickets")
    print("  rung that answered, per ticket:")
    for n, r in enumerate(rungs_used, 1):
        print("    ticket " + str(n) + "  " + ("■" * r).ljust(8) + " " + world.LADDER[r - 1][0])
    print("  --debug answered nothing that a cheaper rung could; it answered the one that only a log can (timing).")
    print_bill()
