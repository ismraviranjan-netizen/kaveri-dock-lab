# D1 · common.py — the shared desk: the DRY_RUN switch, the model tiers, ask()/ask_json()/ask_async(),
# the canned world, and a scripted stand-in client so every exhibit runs with zero paid calls.
#
# DRY_RUN=1  -> make_client() returns FakeClient: same control flow, scripted replies, no network, no bill.
# unset      -> the real anthropic SDK (pip install anthropic; ANTHROPIC_API_KEY in the environment).
# D1_SCENARIO=default|truncate|refuse|exhaust steers the stand-in's final reply, so E7's branches can be watched.
import asyncio, itertools, json, os, re
from pathlib import Path
from types import SimpleNamespace

# Optional .env next to this file (or in the repo root): KEY=value lines, loaded only if the variable is not already set.
# The file is in .gitignore. Never commit the key.
for _env in (Path(__file__).with_name(".env"), Path(__file__).resolve().parent.parent / ".env"):
    if _env.exists():
        for _line in _env.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

DRY_RUN  = os.environ.get("DRY_RUN") == "1"
SCENARIO = os.environ.get("D1_SCENARIO", "default")

# Model tiers. IDs checked against the current API reference (the book's Sep-2026 alias was claude-sonnet-5).
MODEL_MAIN  = "claude-opus-5-5"      # judgement and money
MODEL_MID   = "claude-sonnet-5-5"    # explanation
MODEL_SMALL = "claude-haiku-4-5"     # one-word sorts, templated apologies
MAX_TOKENS  = 1024                   # the book used 500-1000; thinking tokens count toward this on current models

DATA       = Path(__file__).with_name("data")
EMAIL      = (DATA / "padma_email.txt").read_text(encoding="utf-8")
CLAIM_TEXT = (DATA / "refund_claim.txt").read_text(encoding="utf-8")
BRIEF      = (DATA / "brief_kf2481.txt").read_text(encoding="utf-8")

# The two kaveri tools, as schemas. They mirror ../e1_kaveri_mcp.py from the Domain 3 lab.
TOOLS_KAVERI = [
    {"name": "get_shipment_status",
     "description": "Live status for one Kaveri consignment id (e.g. KF-2481).",
     "input_schema": {"type": "object",
                      "properties": {"consignment_id": {"type": "string"}},
                      "required": ["consignment_id"]}},
    {"name": "find_alternate_carriers",
     "description": "Carriers that can take a lane (e.g. Pune-Chennai) within 48 hours.",
     "input_schema": {"type": "object",
                      "properties": {"lane": {"type": "string"}},
                      "required": ["lane"]}},
]


# ── the canned world: tools still answer the phone when the building is on battery ────────────
def fake_status(cid):
    return {"id": cid, "status": "CUSTOMS_HOLD", "missing": "e-way bill", "days_late": 3}

def fake_carriers(lane):
    return ["BlueDart", "Delhivery"]


# ── helpers every exhibit uses ──────────────────────────────────────────────────────────────────
def text_of(r):
    """The text blocks only. Current models may put thinking blocks first, so never read content[0]."""
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")

def trace(turn, r):
    """One line per paid-or-scripted call: the stop_reason is the clerk's note clipped to the file."""
    names = [b.name for b in r.content if getattr(b, "type", "") == "tool_use"]
    print(f"# turn {turn}  stop_reason={r.stop_reason}" + (f"  ({', '.join(names)})" if names else ""))

def make_client():
    if DRY_RUN:
        return FakeClient()
    import anthropic                                  # only imported on the paid path
    return anthropic.Anthropic()

def ask(model, prompt, max_tokens=MAX_TOKENS):
    """One augmented-LLM call, text in, text out. Checks stop_reason before trusting the text."""
    r = make_client().messages.create(model=model, max_tokens=max_tokens,
                                      messages=[{"role": "user", "content": prompt}])
    if r.stop_reason == "refusal":
        raise RuntimeError(f"model refused: {getattr(r, 'stop_details', None)}")
    return text_of(r).strip()

def ask_json(model, prompt, max_tokens=MAX_TOKENS):
    """ask(), then parse JSON. Strips a ```json fence if the model added one."""
    raw = ask(model, prompt, max_tokens)
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    return json.loads(raw)

async def ask_async(model, prompt, max_tokens=256):
    """The async twin, for E4. On battery it sleeps 0.2 s so the slowest-scout lesson is visible."""
    if DRY_RUN:
        await asyncio.sleep(0.2)
        return _canned_text(prompt)
    import anthropic
    r = await anthropic.AsyncAnthropic().messages.create(model=model, max_tokens=max_tokens,
                                                         messages=[{"role": "user", "content": prompt}])
    return text_of(r).strip()


# ── the scripted stand-in: a fake Messages API that reads the conversation and answers in character ──
_votes  = itertools.count()          # E4 voting: APPROVE, REJECT, APPROVE -> majority APPROVE
_rubric = itertools.count()          # E6: first evaluation criticises, second says PASS

DRAFT_FIRST = ("Dear Ms Deshmukh, thank you for reaching out to us regarding consignment KF-2481, and please accept "
               "our sincere apologies for the delay and for the lack of detail on the portal. I have checked the "
               "consignment personally and can confirm it is currently held at the Chennai inland container depot "
               "for a customs document check; specifically, the e-way bill attached to the shipment did not match "
               "the invoice value. Our team is re-filing the corrected bill today and we expect the depot to release "
               "the cartons within twenty-four hours of acceptance. Because of the inconvenience this has caused you "
               "and your buyer, we will refund your shipping charges in full and upgrade your next three shipments "
               "to express at no cost. I will send you the revised ETA personally as soon as the officer confirms "
               "release. Warm regards, KAVI for Kaveri Freight.")
CRITICISM   = ("Over 120 words, and 'we will refund your shipping charges in full' promises compensation the desk "
               "has not approved.")
DRAFT_GOOD  = ("Dear Ms Deshmukh, thank you for your message about KF-2481, and I am sorry for the delay and the "
               "silence on the portal. The consignment is held at the Chennai depot for a customs document check: "
               "the e-way bill did not match the invoice value. We are re-filing the corrected bill today, and the "
               "depot normally releases within a day of accepting it. I will send you the revised delivery time the "
               "moment the officer confirms. Your buyer may quote reference KF-2481 to us directly if that helps. "
               "Regards, KAVI for Kaveri Freight.")
PLAN_JSON   = ('[{"id": 1, "task": "status check", "needs": []}, '
               '{"id": 2, "task": "carrier options", "needs": [1]}, '
               '{"id": 3, "task": "re-route quote", "needs": [2]}]')
FINDINGS    = {"status check":    "CUSTOMS_HOLD at Chennai depot; missing e-way bill; 3 days late",
               "carrier options": "BlueDart 2 days, Delhivery 3 days on Pune-Chennai; both need customs release first",
               "re-route quote":  "Re-route quote Rs 2,400 via BlueDart; only useful after customs release",
               "file e-way bill": "Corrected e-way bill filed per SOP 214 section 4; expected release within 24 h",
               "notify padma":    "Draft ready: revised ETA Saturday, goodwill note, no compensation promised"}
RECOMMENDATION = ("RECOMMENDATION: file the e-way bill today; hold the re-route (costlier than the 24h release); "
                  "send Padma the revised ETA with a goodwill note.")
FINAL_E7    = ("KF-2481 is held at customs for a missing e-way bill. Options: file the bill (fastest, release ~24 h), "
               "or re-route via BlueDart/Delhivery once released. Recommend filing today and telling Padma the revised ETA.")


def _canned_text(prompt):
    p = prompt.lower()
    if "category only" in p:                         return "customs"
    if "approve or reject" in p:                     return "REJECT" if next(_votes) % 3 == 1 else "APPROVE"
    if "eta for" in p:
        m = re.search(r"via (\w+)", prompt);         return f"{m.group(1) if m else 'carrier'}: Thu 16:00, held at customs until release"
    if "rubric:" in p:                               return CRITICISM if next(_rubric) == 0 else "PASS"
    if "revise." in p:                               return DRAFT_GOOD
    if "list 2-5 subtasks" in p:                     return PLAN_JSON
    if "does the remaining plan still hold" in p:
        if "customs_hold" in p and "re-route" in p:
            return json.dumps({"ok": False, "drop": [3], "add": ["file e-way bill", "notify Padma of revised ETA"]})
        return json.dumps({"ok": True})
    if "synthesise" in p:                            return RECOMMENDATION
    if "subtask:" in p:
        for key, val in FINDINGS.items():
            if key in p: return val
        return "no finding"
    if "draft a courteous reply" in p:               return DRAFT_GOOD
    if "reply to this exception email" in p:         return DRAFT_FIRST
    if "refund disputes" in p:                       return "Refund ward: claim acknowledged; verifying the damage note and insurance cover before any decision. No promise made."
    if "customs holds" in p:                         return "Customs ward: KF-2481 is held for an e-way bill mismatch. Next steps: re-file the corrected bill (SOP 214 section 4), expect release within 24 h."
    if "delay apologies" in p:                       return "Delay ward: We are sorry KF-2481 is late. New ETA: Saturday. We will confirm once the depot releases it."
    return "dry-run reply"


def _block(**kw): return SimpleNamespace(**kw)

def _resp(blocks, stop, **extra):
    return SimpleNamespace(content=blocks, stop_reason=stop,
                           usage=SimpleNamespace(input_tokens=0, output_tokens=0), **extra)


def _field(block, name):
    """Read a content-block field whether the block is an SDK object or a plain dict."""
    return block.get(name) if isinstance(block, dict) else getattr(block, name, None)

class _FakeMessages:
    def __init__(self): self.calls = 0

    def create(self, *, model, max_tokens, messages, system=None, tools=None, **_):
        self.calls += 1
        if tools:
            return self._with_tools(messages, system or "", tools)
        last = messages[-1]["content"]
        prompt = last if isinstance(last, str) else " ".join(b.get("text", "") for b in last if isinstance(b, dict))
        return _resp([_block(type="text", text=_canned_text(prompt))], "end_turn")

    def _with_tools(self, messages, system, tools):
        # Read the stateless transcript: which tool requests already have receipts?
        id_to_name, answered = {}, set()
        for m in messages:
            c = m["content"]
            if m["role"] == "assistant" and not isinstance(c, str):
                for b in c:                           # blocks may be SDK objects or plain dicts; the API takes both
                    if _field(b, "type") == "tool_use": id_to_name[_field(b, "id")] = _field(b, "name")
            if m["role"] == "user" and isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        answered.add(id_to_name.get(b["tool_use_id"]))
        transcript = json.dumps(messages, default=str)
        cid = (re.search(r"KF-\d{4}", transcript) or re.search(r"KF-\d{4}", "KF-2481")).group()

        if SCENARIO == "exhaust":                     # a detective who never stops asking for the phone
            return _resp([_block(type="tool_use", id=f"toolu_dry_{self.calls}",
                                 name="get_shipment_status", input={"consignment_id": cid})], "tool_use")
        for t in tools:                               # first unanswered tool gets called
            if t["name"] not in answered:
                inp = {"consignment_id": cid} if t["name"] == "get_shipment_status" else {"lane": "Pune-Chennai"}
                return _resp([_block(type="tool_use", id=f"toolu_dry_{self.calls}", name=t["name"], input=inp)],
                             "tool_use")
        # every tool answered: the finale, steered by the scenario
        if SCENARIO == "refuse":
            return _resp([], "refusal",
                         stop_details=SimpleNamespace(type="refusal", category="general_harms",
                                                      explanation="scripted dry-run refusal"))
        final = '{"category": "customs", "urgency": "high"}' if "triage" in system.lower() else FINAL_E7
        continued = any(m["role"] == "user" and m["content"] == "Continue." for m in messages)
        if SCENARIO == "truncate" and not continued:
            cut = len(final) // 2
            return _resp([_block(type="text", text=final[:cut])], "max_tokens")
        if SCENARIO == "truncate" and continued:
            return _resp([_block(type="text", text=final[len(final) // 2:])], "end_turn")
        return _resp([_block(type="text", text=final)], "end_turn")


class FakeClient:
    def __init__(self): self.messages = _FakeMessages()
