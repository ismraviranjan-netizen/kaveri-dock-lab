# common.py  -  the shared desk for the eight Domain 1 exhibits.
#
# Every exhibit imports from here, so the things that never change live in one place:
#   STEP A  the two switches (DRY_RUN, D1_SCENARIO) and the optional .env loader
#   STEP B  which models to use, and how long a reply may be
#   STEP C  the three inputs: Padma's email, the refund claim, Meera's brief (read from data/)
#   STEP D  the two tool DESCRIPTIONS (schemas) the model may ask for
#   STEP E  the tools THEMSELVES: plain Python that answers from a canned world
#   STEP F  helpers: text_of(), trace(), make_client(), ask(), ask_json(), ask_async()
#
# DRY_RUN=1  -> make_client() returns the scripted stand-in from standin.py:
#               same control flow, canned replies, no network, no bill.
# unset      -> the real anthropic SDK. Needs:  pip install anthropic
#               and ANTHROPIC_API_KEY in the environment, or in a .env file in the repo root (git-ignored).

import asyncio
import json
import os
import re
from pathlib import Path


# ---------------------------------------------------------------
# STEP A. Switches, and the optional .env loader
# ---------------------------------------------------------------

# If a .env file exists (next to this file, or in the repo root), copy its KEY=value lines into the
# environment. A variable that is already set wins. The file is git-ignored: never commit the key.
for env_file in (Path(__file__).with_name(".env"), Path(__file__).resolve().parent.parent / ".env"):
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line == "" or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

DRY_RUN = os.environ.get("DRY_RUN") == "1"              # battery mode: stand-in client, zero paid calls
SCENARIO = os.environ.get("D1_SCENARIO", "default")      # steers the stand-in's final reply in E7


# ---------------------------------------------------------------
# STEP B. Models and reply length
# ---------------------------------------------------------------

MODEL_MAIN = "claude-sonnet-5-5"    # judgement, planning, drafting, synthesis
MODEL_SMALL = "claude-haiku-4-5"    # one-word sorts, small workers, short apologies
MAX_TOKENS = 1024                   # the longest reply we accept; thinking tokens count toward it
# Production would put refunds and planning on the Opus tier (claude-opus-5-5).
# Sonnet is used here so a learning run stays cheap. Change the one constant above to switch.


# ---------------------------------------------------------------
# STEP C. The three inputs, read from the data/ folder
# ---------------------------------------------------------------

DATA = Path(__file__).with_name("data")
EMAIL = (DATA / "padma_email.txt").read_text(encoding="utf-8")        # E1, E2, E3, E6
CLAIM_TEXT = (DATA / "refund_claim.txt").read_text(encoding="utf-8")  # E4 voting
BRIEF = (DATA / "brief_kf2481.txt").read_text(encoding="utf-8")       # E5, E8


# ---------------------------------------------------------------
# STEP D. The two tool descriptions. A schema is a phone-book entry:
#         name, what it does, what input it needs. It is NOT the code.
# ---------------------------------------------------------------

TOOLS_KAVERI = [
    {
        "name": "get_shipment_status",
        "description": "Live status for one Kaveri consignment id (e.g. KF-2481).",
        "input_schema": {
            "type": "object",
            "properties": {"consignment_id": {"type": "string"}},
            "required": ["consignment_id"],
        },
    },
    {
        "name": "find_alternate_carriers",
        "description": "Carriers that can take a lane (e.g. Pune-Chennai) within 48 hours.",
        "input_schema": {
            "type": "object",
            "properties": {"lane": {"type": "string"}},
            "required": ["lane"],
        },
    },
]


# ---------------------------------------------------------------
# STEP E. The tools themselves. Plain Python. The model never sees this code.
#         In production these would query the depot database or the MCP server.
# ---------------------------------------------------------------

def fake_status(consignment_id):
    return {"id": consignment_id, "status": "CUSTOMS_HOLD", "missing": "e-way bill", "days_late": 3}


def fake_carriers(lane):
    return ["BlueDart", "Delhivery"]


# ---------------------------------------------------------------
# STEP F. Helpers every exhibit uses
# ---------------------------------------------------------------

def text_of(reply):
    """Collect the text blocks only. Never read content[0]: a thinking block may come first."""
    answer = ""
    for block in reply.content:
        if block.type == "text":
            answer = answer + block.text
    return answer


def trace(turn, reply):
    """Print one line per call: the turn number, the stop_reason, and any tools the model asked for."""
    tool_names = []
    for block in reply.content:
        if block.type == "tool_use":
            tool_names.append(block.name)
    line = "# turn " + str(turn) + "  stop_reason=" + str(reply.stop_reason)
    if tool_names:
        line = line + "  (" + ", ".join(tool_names) + ")"
    print(line)


def _sdk_kwargs():
    """An org-level key must name a workspace on every request. Set ANTHROPIC_WORKSPACE_ID in .env,
    or use a key created inside a workspace, in which case this header is not needed."""
    workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    if workspace:
        return {"default_headers": {"anthropic-workspace-id": workspace}}
    return {}


def make_client():
    """The stand-in on battery, the real SDK live. The exhibits do not know or care which one they got."""
    if DRY_RUN:
        from standin import FakeClient
        return FakeClient()
    import anthropic                                  # only imported on the paid path
    return anthropic.Anthropic(**_sdk_kwargs())


def ask(model, question, system=None, max_tokens=MAX_TOKENS):
    """One call, text in, text out. No tools. Checks stop_reason before trusting the text."""
    arguments = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": question}],
    }
    if system is not None:
        arguments["system"] = system

    reply = make_client().messages.create(**arguments)

    if reply.stop_reason == "refusal":
        raise RuntimeError("The model declined to answer.")
    return text_of(reply).strip()


def ask_json(model, question, max_tokens=MAX_TOKENS):
    """ask(), then parse the reply as JSON. Models sometimes wrap JSON in a ```json fence; strip it."""
    raw = ask(model, question, max_tokens=max_tokens)
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:]                        # drop the opening ```json line
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]                   # drop the closing ``` line
        raw = "\n".join(lines)
    return json.loads(raw)


async def ask_async(model, question, max_tokens=256):
    """The async twin of ask(), for E4. On battery it sleeps 0.2 s so the slowest-scout lesson is visible."""
    if DRY_RUN:
        from standin import canned_text
        await asyncio.sleep(0.2)
        return canned_text(None, question)

    import anthropic
    client = anthropic.AsyncAnthropic(**_sdk_kwargs())
    reply = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": question}],
    )
    if reply.stop_reason == "refusal":
        raise RuntimeError("The model declined to answer.")
    return text_of(reply).strip()
