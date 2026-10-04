# standin.py  -  a scripted stand-in for the Messages API, used when DRY_RUN=1.
#
# You do not need to read this file to learn the patterns. It exists so every exhibit can run its real
# control flow (the same stop_reason branches, the same replayed transcript) with zero paid calls.
# It reads the conversation it is given and answers in character:
#   - with tools attached, it asks for the first tool that has no result yet, then gives a finale
#   - without tools, it matches a few words in the prompt and returns a canned reply
# D1_SCENARIO=default|truncate|refuse|exhaust changes the finale so E7's branches can be watched.

import itertools
import json
import os
import re
from types import SimpleNamespace

SCENARIO = os.environ.get("D1_SCENARIO", "default")

# ---------------------------------------------------------------
# The canned world: fixed texts the stand-in hands back
# ---------------------------------------------------------------

DRAFT_FIRST = ("Dear Ms Deshmukh, thank you for reaching out to us regarding consignment KF-2481, and please accept "
               "our sincere apologies for the delay and for the lack of detail on the portal. I have checked the "
               "consignment personally and can confirm it is currently held at the Chennai inland container depot "
               "for a customs document check; specifically, the e-way bill attached to the shipment did not match "
               "the invoice value. Our team is re-filing the corrected bill today and we expect the depot to release "
               "the cartons within twenty-four hours of acceptance. Because of the inconvenience this has caused you "
               "and your buyer, we will refund your shipping charges in full and upgrade your next three shipments "
               "to express at no cost. I will send you the revised ETA personally as soon as the officer confirms "
               "release. Warm regards, KAVI for Kaveri Freight.")
CRITICISM = ("Over 120 words, and 'we will refund your shipping charges in full' promises compensation the desk "
             "has not approved.")
DRAFT_GOOD = ("Dear Ms Deshmukh, thank you for your message about KF-2481, and I am sorry for the delay and the "
              "silence on the portal. The consignment is held at the Chennai depot for a customs document check: "
              "the e-way bill did not match the invoice value. We are re-filing the corrected bill today, and the "
              "depot normally releases within a day of accepting it. I will send you the revised delivery time the "
              "moment the officer confirms. Your buyer may quote reference KF-2481 to us directly if that helps. "
              "Regards, KAVI for Kaveri Freight.")
PLAN_JSON = ('[{"id": 1, "task": "status check", "needs": []}, '
             '{"id": 2, "task": "carrier options", "needs": [1]}, '
             '{"id": 3, "task": "re-route quote", "needs": [2]}]')
FINDINGS = {
    "status check":    "CUSTOMS_HOLD at Chennai depot; missing e-way bill; 3 days late",
    "carrier options": "BlueDart 2 days, Delhivery 3 days on Pune-Chennai; both need customs release first",
    "re-route quote":  "Re-route quote Rs 2,400 via BlueDart; only useful after customs release",
    "file e-way bill": "Corrected e-way bill filed per SOP 214 section 4; expected release within 24 h",
    "notify padma":    "Draft ready: revised ETA Saturday, goodwill note, no compensation promised",
}
RECOMMENDATION = ("RECOMMENDATION: file the e-way bill today; hold the re-route (costlier than the 24h release); "
                  "send Padma the revised ETA with a goodwill note.")
FINAL_E7 = ("KF-2481 is held at customs for a missing e-way bill. Options: file the bill (fastest, release ~24 h), "
            "or re-route via BlueDart/Delhivery once released. Recommend filing today and telling Padma the revised ETA.")

_votes = itertools.count()     # E4 voting: APPROVE, REJECT, APPROVE -> majority APPROVE
_rubric = itertools.count()    # E6: the first evaluation criticises, the second says PASS


def canned_text(system, prompt):
    """Match a few words in the system prompt and the user prompt, return the matching canned reply."""
    p = (system or "").lower() + "\n" + prompt.lower()

    if "one word only" in p:                          # E2 desk 1, E3 nurse
        return "customs"
    if "approve or reject" in p:                      # E4 voting
        return "REJECT" if next(_votes) % 3 == 1 else "APPROVE"
    if "eta for" in p:                                # E4 scouts
        m = re.search(r"via (\w+)", prompt)
        carrier = m.group(1) if m else "carrier"
        return carrier + ": Thu 16:00, held at customs until release"
    if "rubric:" in p:                                # E6 editor
        return CRITICISM if next(_rubric) == 0 else "PASS"
    if "revise the draft" in p:                       # E6 writer, second pass
        return DRAFT_GOOD
    if "break this into" in p:                        # E5 foreman
        return PLAN_JSON
    if "remaining plan" in p:                         # E8 check after a finding
        if "customs_hold" in p and "re-route" in p:
            return json.dumps({"ok": False, "drop": [3], "add": ["file e-way bill", "notify Padma of revised ETA"]})
        return json.dumps({"ok": True})
    if "recommendation for meera" in p:               # E5 and E8 synthesis
        return RECOMMENDATION
    if "subtask:" in p:                               # E5 and E8 workers
        m = re.search(r"subtask: (.+)", p)
        name = m.group(1).strip() if m else ""
        for key, value in FINDINGS.items():
            if name.startswith(key):
                return value
        return "no finding"
    if "draft a courteous reply" in p:                # E2 desk 2
        return DRAFT_GOOD
    if "exception email" in p:                        # E6 first draft (deliberately too long, promises a refund)
        return DRAFT_FIRST
    if "refund disputes" in p:                        # E3 wards
        return "Refund ward: claim acknowledged; verifying the damage note and insurance cover before any decision. No promise made."
    if "customs holds" in p:
        return "Customs ward: KF-2481 is held for an e-way bill mismatch. Next steps: re-file the corrected bill (SOP 214 section 4), expect release within 24 h."
    if "delay apologies" in p:
        return "Delay ward: We are sorry KF-2481 is late. New ETA: Saturday. We will confirm once the depot releases it."
    return "dry-run reply"


# ---------------------------------------------------------------
# Reply objects shaped like the SDK's: .content (a list of blocks), .stop_reason, .usage
# ---------------------------------------------------------------

def _block(**fields):
    return SimpleNamespace(**fields)


def _reply(blocks, stop_reason, **extra):
    return SimpleNamespace(content=blocks, stop_reason=stop_reason,
                           usage=SimpleNamespace(input_tokens=0, output_tokens=0), **extra)


def _field(block, name):
    """Read a content-block field whether the block is an SDK object or a plain dict. The API takes both."""
    if isinstance(block, dict):
        return block.get(name)
    return getattr(block, name, None)


class _FakeMessages:
    def __init__(self):
        self.calls = 0

    def create(self, *, model, max_tokens, messages, system=None, tools=None, **_):
        self.calls = self.calls + 1
        if tools:
            return self._with_tools(messages, system or "", tools)

        # No tools: answer the last user message from the canned world.
        last = messages[-1]["content"]
        if isinstance(last, str):
            prompt = last
        else:
            prompt = " ".join(b.get("text", "") for b in last if isinstance(b, dict))
        return _reply([_block(type="text", text=canned_text(system, prompt))], "end_turn")

    def _with_tools(self, messages, system, tools):
        # Read the stateless transcript: which tool requests already have a result?
        id_to_name = {}
        answered = set()
        for message in messages:
            content = message["content"]
            if message["role"] == "assistant" and not isinstance(content, str):
                for block in content:
                    if _field(block, "type") == "tool_use":
                        id_to_name[_field(block, "id")] = _field(block, "name")
            if message["role"] == "user" and isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        answered.add(id_to_name.get(block["tool_use_id"]))

        transcript = json.dumps(messages, default=str)
        found = re.search(r"KF-\d{4}", transcript)
        consignment_id = found.group() if found else "KF-2481"

        if SCENARIO == "exhaust":                     # a detective who never stops asking for the phone
            return _reply([_block(type="tool_use", id="toolu_dry_" + str(self.calls),
                                  name="get_shipment_status", input={"consignment_id": consignment_id})], "tool_use")

        for tool in tools:                            # the first tool with no result yet gets called
            if tool["name"] not in answered:
                if tool["name"] == "get_shipment_status":
                    tool_input = {"consignment_id": consignment_id}
                else:
                    tool_input = {"lane": "Pune-Chennai"}
                return _reply([_block(type="tool_use", id="toolu_dry_" + str(self.calls),
                                      name=tool["name"], input=tool_input)], "tool_use")

        # Every tool answered: the finale, steered by the scenario.
        if SCENARIO == "refuse":
            return _reply([], "refusal",
                          stop_details=SimpleNamespace(type="refusal", category="general_harms",
                                                       explanation="scripted dry-run refusal"))

        if "triage" in system.lower():
            final = '{"category": "customs", "urgency": "high"}'
        else:
            final = FINAL_E7

        continued = False
        for message in messages:
            if message["role"] == "user" and message["content"] == "Continue.":
                continued = True

        if SCENARIO == "truncate" and not continued:
            cut = len(final) // 2
            return _reply([_block(type="text", text=final[:cut])], "max_tokens")
        if SCENARIO == "truncate" and continued:
            return _reply([_block(type="text", text=final[len(final) // 2:])], "end_turn")
        return _reply([_block(type="text", text=final)], "end_turn")


class FakeClient:
    def __init__(self):
        self.messages = _FakeMessages()
