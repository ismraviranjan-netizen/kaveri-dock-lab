# standin.py  -  a scripted stand-in for the Messages API, used when DRY_RUN=1.
#
# You do not need to read this file to learn the patterns. It exists so every exhibit can run its real
# control flow with zero paid calls. It counts tokens at about four characters each, invents a thinking
# count from the effort dial, honours cache_control the way the API does (write once, read after), returns
# a 400 for a manual thinking budget, and answers from a canned world by matching words in the prompt.

import json
import re
from types import SimpleNamespace

THINK_BY_EFFORT = {"low": 60, "medium": 220, "high": 700}   # invented thinking tokens per call, by effort
CACHE_MIN = 512                                               # Fable caches nothing shorter than this

_cache_seen = set()                                           # prefixes written in this process


class BadRequestError(Exception):
    status_code = 400


def _tokens(text):
    return max(1, len(text) // 4)


def _classify(text):
    t = text.lower()
    if any(w in t for w in ("customs", "e-way", "invoice", "duty", "hsn", "entry", "icd", "jnpt")):
        return "customs_hold"
    if any(w in t for w in ("house", "pincode", "address", "flat", "gate", "consignee", "street", "label")):
        return "address_fail"
    if any(w in t for w in ("broken", "crushed", "damage", "cracked", "wet", "seal")):
        return "damage"
    return "delay"


def canned_text(system_text, prompt):
    s = system_text.lower()
    p = prompt.lower()
    if "name the exception type" in s:
        return _classify(prompt)
    if "<caller_said>" in p:
        return json.dumps({"reply": "Ji, 7,800 ka refund supervisor approve karenge; main escalate kar raha hoon.",
                           "quoted_amount_inr": 7800, "escalate": False, "sop_section": "SOP 214 s7"})
    if "summarise this dispatcher thread" in s:
        return ("Open issues: KF-2401 to KF-2432 each reported in transit via Pune hub with a six-hour ETA; no "
                "exceptions raised, no customer promises made, all awaiting the next carrier scan.")
    if "at most three sentences" in s:
        return ("Pull the officer's remark from the TMS hold record and identify the mismatched field. Ask billing "
                "for a corrected invoice if the value is wrong, then re-file the e-way bill on the portal. Email the "
                "new bill number to the depot officer and do not promise the customer a release time.")
    if "one short sentence" in s:
        return "Check that the e-way bill was filed today and re-file it before 6 pm if it was not."
    if "customs hold" in p or "held at customs" in p:
        return "First check whether the e-way bill was filed today; if not, re-file it under SOP 214 s4."
    return "dry-run reply"


def _system_text(system):
    if system is None:
        return ""
    if isinstance(system, str):
        return system
    return "\n".join(block.get("text", "") for block in system)


def _cache_usage(system):
    """Mimic prompt caching: the text up to the last cache_control block is the prefix. First sight writes it,
    later sights read it, and nothing under CACHE_MIN tokens is cached at all."""
    if not isinstance(system, list):
        return 0, 0
    prefix = ""
    marked = False
    for block in system:
        prefix = prefix + block.get("text", "")
        if "cache_control" in block:
            marked = True
    if not marked or _tokens(prefix) < CACHE_MIN:
        return 0, 0
    if prefix in _cache_seen:
        return 0, _tokens(prefix)
    _cache_seen.add(prefix)
    return _tokens(prefix), 0


class _FakeMessages:
    def create(self, *, model, max_tokens, messages, system=None, output_config=None, thinking=None, **_):
        if thinking and thinking.get("budget_tokens"):
            raise BadRequestError("thinking.budget_tokens is not supported on " + model)
        system_text = _system_text(system)
        last = messages[-1]["content"]
        prompt = last if isinstance(last, str) else " ".join(b.get("text", "") for b in last if isinstance(b, dict))
        answer = canned_text(system_text, prompt)
        effort = (output_config or {}).get("effort", "high")
        think = THINK_BY_EFFORT.get(effort, 700)
        written, read = _cache_usage(system)
        prompt_tokens = _tokens(json.dumps(messages)) + _tokens(system_text)
        usage = SimpleNamespace(input_tokens=max(1, prompt_tokens - written - read), output_tokens=_tokens(answer) + think,
                                output_tokens_details=SimpleNamespace(thinking_tokens=think),
                                cache_creation_input_tokens=written, cache_read_input_tokens=read)
        return SimpleNamespace(content=[SimpleNamespace(type="thinking", thinking=""),
                                        SimpleNamespace(type="text", text=answer)],
                               stop_reason="end_turn", usage=usage, model=model)

    def count_tokens(self, *, model, messages, system=None, **_):
        return SimpleNamespace(input_tokens=_tokens(json.dumps(messages)) + _tokens(_system_text(system)))


class _FakeSkills:
    def list(self, **_):
        return []

    def create(self, *, display_name, files, **_):
        return SimpleNamespace(id="skill_dry_" + display_name, display_name=display_name)


class FakeClient:
    def __init__(self):
        self.messages = _FakeMessages()
        self.skills = _FakeSkills()
        self.beta = SimpleNamespace(messages=self.messages)
