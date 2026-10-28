# standin.py  -  the DRY_RUN stand-in for d7. Answers in character, with one deliberate slip per exhibit so the
# grading has something to catch on battery. Not needed to learn the patterns.

import json
from types import SimpleNamespace

LADDER_ANSWERS = [("personal key", "/status"), ("never fires", "/hooks"), ("carrier-portal", "/mcp"),
                  ("curl", "/permissions"), ("docs/claude.md", "/context"), ("changelog", "/debug_slip"),
                  ("guard hook", "--debug")]
QUIZ = [("rm -rf", "B", {"A": "SD", "C": "CM", "D": "CM"}), ("carrier-portal", "A", {"B": "OE", "C": "OE", "D": "OE"}),
        ("contractor", "B", {"A": "OP", "C": "TR", "D": "VG"}), ("refund", "B", {"A": "HL", "C": "SD", "D": "CM"}),
        ("every developer", "A", {"B": "OE", "C": "CM", "D": "CM"})]


def _answer(system, prompt):
    prompt = prompt.lower()
    if "debug ladder" in system:
        for clue, cmd in LADDER_ANSWERS:
            if clue in prompt:
                return {"command": "--debug" if cmd == "/debug_slip" else cmd, "why": "dry-run guess"}
    if "permission mode" in system:
        import e2_permission_modes as e2
        grid = [{"action": a, "outcomes": [e2.decide(m, a, k, r)[0] for m in e2.MODES]} for a, k, r in e2.ACTIONS]
        grid[5]["outcomes"][1] = "ALLOW"                     # the slip: thinks acceptEdits allows git push
        return {"grid": grid}
    if "certification question" in system:
        for clue, key, fams in QUIZ:
            if clue in prompt:
                return {"answer": key, "families": [{"option": k, "family": v} for k, v in fams.items()]}
    return {}


class _Messages:
    def create(self, *, model, system="", messages, **_):
        text = json.dumps(_answer(system, messages[-1]["content"]))
        usage = SimpleNamespace(input_tokens=(len(system) + len(messages[-1]["content"])) // 4, output_tokens=len(text) // 4 + 60)
        return SimpleNamespace(content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
                               stop_reason="end_turn", usage=usage, model=model)


class FakeClient:
    def __init__(self):
        self.messages = _Messages()
        self.beta = SimpleNamespace(messages=self.messages)
