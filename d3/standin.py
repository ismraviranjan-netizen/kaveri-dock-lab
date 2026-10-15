# standin.py  -  a scripted stand-in for the Messages API, used when DRY_RUN=1.
#
# You do not need to read this file to learn the patterns. It exists so every exhibit can run its real
# control flow (the same stop_reason branches, the same tool_result round-trips) with zero paid calls.
# It reads the conversation it is given and answers in character:
#   - with tools attached, it asks for the first tool that has no result yet, then gives a finale
#   - without tools, it matches a few words in the prompt and returns a canned reply
#   - count_tokens() is the free bench: about four characters per token

import json
import re
from types import SimpleNamespace


# ---------------------------------------------------------------
# The canned world: fixed texts the stand-in hands back
# ---------------------------------------------------------------

DRAFT_REFILE = ("KF-2481 is held at ICD Pune for an e-way bill mismatch. Follow SOP 214 section 4: pull the officer's "
                "remark, get a corrected invoice if the value is wrong, extend or generate the bill on the portal, "
                "enter the corrected details, submit and attach it tagged re-filed, then email the new bill number to "
                "the depot officer. The hold lifts only when the officer confirms. No release time is promised.")
FINAL_E1 = ("KF-2481 is in CUSTOMS_HOLD at ICD Pune, missing its e-way bill. Per SOP 214 section 4, re-file: identify "
            "the flagged field, correct the invoice if needed, extend or regenerate the bill, attach it tagged re-filed, "
            "and email the officer. Do not promise a release date until the officer confirms.")
FINAL_DENIED = ("I could not process the refund: the tool was denied (kavi-agent lacks refund:write). The consignment "
                "KF-2481 is in CUSTOMS_HOLD. I am escalating the refund request to the operations lead instead.")
FINAL_REFUNDED = "Refund of 4200 INR processed on KF-2481."


def _steps_in(excerpt):
    """E4: which 'Step N' labels appear in the excerpt the prompt carried? The stand-in reads, it does not know."""
    excerpt = excerpt.split("EXCERPT:", 1)[-1]           # read the excerpt, not the question that names Step 1 to 6
    found = sorted(set(int(n) for n in re.findall(r"Step (\d)", excerpt)))
    missing = [n for n in range(1, 7) if n not in found]
    line = "Steps present in the excerpt: " + ", ".join(str(n) for n in found) + "."
    if missing:
        line = line + " MISSING: Step " + ", Step ".join(str(n) for n in missing) + ". The procedure is incomplete here."
    else:
        line = line + " All six re-filing steps are present. The procedure is complete here."
    return line


def canned_text(system, prompt):
    """Match a few words in the system prompt and the user prompt, return the matching canned reply."""
    p = (system or "").lower() + "\n" + prompt.lower()

    if "using only the excerpt" in p:                 # E4: answer from one chunk
        return _steps_in(prompt)
    if "score each section" in p:                     # E5: the live foreman would score chunk titles
        return "{}"                                   # never reached on battery: e5 uses the toy foreman instead
    if "draft the dispatcher's answer" in p:          # E6, E7, E9 drafts
        return DRAFT_REFILE
    return "dry-run reply"


# ---------------------------------------------------------------
# Reply objects shaped like the SDK's: .content (a list of blocks), .stop_reason, .usage
# ---------------------------------------------------------------

def _block(**fields):
    return SimpleNamespace(**fields)


def _reply(blocks, stop_reason, prompt_chars=0):
    out_chars = sum(len(getattr(b, "text", "")) for b in blocks)
    usage = SimpleNamespace(input_tokens=prompt_chars // 4, output_tokens=out_chars // 4)
    return SimpleNamespace(content=blocks, stop_reason=stop_reason, usage=usage)


def _field(block, name):
    """Read a content-block field whether the block is an SDK object or a plain dict. The API takes both."""
    if isinstance(block, dict):
        return block.get(name)
    return getattr(block, name, None)


def _guess_input(schema):
    """Fill a tool's required fields with the canned world's values, so the dispatch code sees real shapes."""
    values = {"consignment_id": "KF-2481", "lane": "Pune-Chennai", "amount_inr": 4200,
              "reason": "customs hold, three days late", "summary": "refund denied at the gate; customs hold on KF-2481",
              "urgency": "high", "order_id": "ORD-10231", "customer_id": "C-77", "depot": "ICD Pune",
              "invoice_no": "INV-5512", "vehicle_no": "MH12AB1234", "phone": "+91-98xxxxxx", "template_id": "hold_notice"}
    filled = {}
    for field in schema.get("input_schema", {}).get("required", []):
        filled[field] = values.get(field, "x")
    return filled


class _FakeMessages:
    def __init__(self):
        self.calls = 0

    def create(self, *, model, max_tokens, messages, system=None, tools=None, **_):
        self.calls = self.calls + 1
        prompt_chars = len(json.dumps(messages, default=str)) + len(system or "")
        if tools:
            return self._with_tools(messages, system or "", tools, prompt_chars)

        # No tools: answer the last user message from the canned world.
        last = messages[-1]["content"]
        if isinstance(last, str):
            prompt = last
        else:
            prompt = " ".join(b.get("text", "") for b in last if isinstance(b, dict))
        return _reply([_block(type="text", text=canned_text(system, prompt))], "end_turn", prompt_chars)

    def count_tokens(self, *, model, messages, tools=None, system=None, **_):
        chars = len(json.dumps(messages)) + len(system or "")
        if tools:
            chars = chars + len(json.dumps(tools))
        return SimpleNamespace(input_tokens=chars // 4)

    def _with_tools(self, messages, system, tools, prompt_chars):
        # Read the stateless transcript: which tool requests already have a result, and did any come back as an error?
        id_to_name = {}
        answered = set()
        denied = False
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
                        if block.get("is_error"):
                            denied = True

        for tool in tools:                            # the first tool with no result yet gets called
            if tool["name"] not in answered:
                if tool["name"] == "escalate_to_human" and not denied:
                    continue                          # only escalate after a door was shut
                return _reply([_block(type="tool_use", id="toolu_dry_" + str(self.calls),
                                      name=tool["name"], input=_guess_input(tool))], "tool_use", prompt_chars)

        # Every tool answered: the finale.
        if denied:
            final = FINAL_DENIED
        elif "process_refund" in answered:
            final = FINAL_REFUNDED
        else:
            final = FINAL_E1
        return _reply([_block(type="text", text=final)], "end_turn", prompt_chars)


class FakeClient:
    def __init__(self):
        self.messages = _FakeMessages()
