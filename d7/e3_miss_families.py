# E3 · Miss families: why the wrong answers are wrong
#
#   Five Domain 7 stems. Each has one right option; every wrong option belongs to a FAMILY of mistake:
#     CM missed the constraint (everyone / unattended / before the tool)   OP over-permissive key
#     SD persuasion instead of control   TR trade-off reversed   VG vocabulary gap   OE over-engineered   HL human loop skipped
#   FABLE picks the answer AND labels the family of each wrong option. The CODE grades both against the key.
#   Run with --me to take the quiz yourself instead (no API call; the code grades you the same way).
#
# Run on battery:  DRY_RUN=1 python e3_miss_families.py     Run live:  python e3_miss_families.py   (5 calls)
# Take it yourself: python e3_miss_families.py --me

import sys
from common import ask_schema, served_by, print_bill, MODEL, DRY_RUN

FAMILIES = {"CM": "missed the constraint", "OP": "over-permissive key", "SD": "persuasion instead of control",
            "TR": "trade-off reversed", "VG": "vocabulary gap", "OE": "over-engineered", "HL": "human loop skipped"}

QUESTIONS = [  # (stem, {letter: option}, right letter, {wrong letter: family}, the tell)
    ("rm -rf must be blocked for every developer on every machine, including unattended CI runs.",
     {"A": "Add 'never run rm -rf' to the project CLAUDE.md",
      "B": "A PreToolUse hook in managed settings that exits with code 2 on rm -rf",
      "C": "A PostToolUse hook in each developer's user settings that logs rm -rf",
      "D": "A deny rule in .claude/settings.local.json"},
     "B", {"A": "SD", "C": "CM", "D": "CM"},
     "every machine + before the tool runs: managed settings, PreToolUse, exit 2"),
    ("The carrier-portal tools have vanished from Claude's tool list. What should the developer run first?",
     {"A": "/mcp",
      "B": "claude --debug, then read the log",
      "C": "Uninstall and reinstall Claude Code",
      "D": "Add mcp__carrier-portal__* to the allow list"},
     "A", {"B": "OE", "C": "OE", "D": "VG"},
     "first + tools missing: the cheapest rung that lists servers and their tools"),
    ("A contractor's machine must run the test suite unattended overnight, and do nothing else.",
     {"A": "bypassPermissions mode on the contractor's laptop",
      "B": "dontAsk mode with an allow rule for Bash(npm test) only",
      "C": "plan mode, so nothing can break",
      "D": "acceptEdits mode"},
     "B", {"A": "OP", "C": "TR", "D": "VG"},
     "unattended + nothing else: deny by default, allow exactly one command"),
    ("A refund command must never run until a person has signed off on it.",
     {"A": "auto mode: the classifier will catch risky refunds",
      "B": "An ask rule for Bash(refund:*)",
      "C": "An allow rule, plus a CLAUDE.md line telling Claude to be careful",
      "D": "A PostToolUse hook that records every refund"},
     "B", {"A": "HL", "C": "SD", "D": "CM"},
     "a person signs off before: an ask rule puts a human in front of the tool"),
    ("Every developer on this repo should share the same allow and deny rules, and they must not apply to other repos.",
     {"A": "Commit them in .claude/settings.json",
      "B": "Push them to every laptop through managed settings",
      "C": "Each developer copies them into ~/.claude/settings.json",
      "D": "Put them in .claude/settings.local.json"},
     "A", {"B": "OE", "C": "CM", "D": "CM"},
     "shared + this repo only: the committed project settings file"),
]

SYSTEM = ("You are sitting a Claude Code certification question. Pick the one correct option, and for every WRONG option "
          "name its mistake family: " + "; ".join(k + " = " + v for k, v in FAMILIES.items()) + ".")
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["answer", "families"],
          "properties": {"answer": {"type": "string", "enum": ["A", "B", "C", "D"]},
                         "families": {"type": "array", "items": {
                             "type": "object", "additionalProperties": False, "required": ["option", "family"],
                             "properties": {"option": {"type": "string", "enum": ["A", "B", "C", "D"]},
                                            "family": {"type": "string", "enum": list(FAMILIES)}}}}}}


def show(n, stem, options):
    print()
    print("--- question " + str(n) + " " + "-" * 78)
    print("  " + stem)
    for letter, text in options.items():
        print("    " + letter + ". " + text)


if __name__ == "__main__":
    me = "--me" in sys.argv
    print("# E3 · miss families · " + ("YOU, graded by code" if me else ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL)))
    print("  families: " + " · ".join(k + " " + v for k, v in FAMILIES.items()))

    answers_right, labels_right, labels_total, family_hits = 0, 0, 0, {k: [0, 0] for k in FAMILIES}
    for n, (stem, options, key, wrong, tell) in enumerate(QUESTIONS, 1):
        show(n, stem, options)
        if me:
            answer = input("  your answer (A-D): ").strip().upper()
            labels = {letter: input("  family of " + letter + " (" + "/".join(FAMILIES) + "): ").strip().upper()
                      for letter in options if letter != answer}
            note = ""
        else:
            guess, reply = ask_schema(SYSTEM, stem + "\n" + "\n".join(l + ". " + t for l, t in options.items()), SCHEMA)
            answer, labels, note = guess["answer"], {f["option"]: f["family"] for f in guess["families"]}, served_by(reply)
        answers_right += answer == key
        print("  answer  : " + answer + ("  ✓" if answer == key else "  ✗ key is " + key) + note)
        for letter, family in wrong.items():
            given = labels.get(letter, "-")
            labels_right += given == family
            labels_total += 1
            family_hits[family][0] += given == family
            family_hits[family][1] += 1
            print("    " + letter + "  key " + family + " (" + FAMILIES[family] + ")".ljust(32 - len(FAMILIES[family]))
                  + "given " + given + ("  ✓" if given == family else "  ✗"))
        print("  the tell: " + tell)

    print()
    print("=== SCORECARD ===")
    print("  answers : " + str(answers_right) + " of " + str(len(QUESTIONS)))
    print("  families: " + str(labels_right) + " of " + str(labels_total))
    print("  by family (labelled right / times it appeared):")
    for k, (hit, seen) in family_hits.items():
        if seen:
            print("    " + k + " " + FAMILIES[k].ljust(32) + ("■" * hit + "□" * (seen - hit)).ljust(5) + " " + str(hit) + "/" + str(seen))
    if not me:
        print_bill()
