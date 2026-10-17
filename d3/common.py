# common.py  -  the shared desk for the nine Domain 3 exhibits (the Loading Dock).
#
# Every exhibit imports from here, so the things that never change live in one place:
#   STEP A  the switch (DRY_RUN) and the optional .env loader
#   STEP B  which models to use, how long a reply may be, and a rough price list
#   STEP C  the inputs: SOP 214, the nine-tool belt, the canned log day (all under data/)
#   STEP D  the tool DESCRIPTIONS the model may ask for, picked out of the belt by name
#   STEP E  the tools THEMSELVES: plain Python that answers from a canned world
#   STEP F  helpers: text_of(), trace(), make_client(), ask(), ask_json(), ask_usage(), count_tokens()
#
# DRY_RUN=1  -> make_client() returns the scripted stand-in from standin.py:
#               same control flow, canned replies, no network, no bill.
# unset      -> the real anthropic SDK. Needs:  pip install anthropic
#               and ANTHROPIC_API_KEY in the environment, or in a .env file in the repo root (git-ignored).

import json
import os
from pathlib import Path


# ---------------------------------------------------------------
# STEP A. The switch, and the optional .env loader
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
PRETTY = os.environ.get("PRETTY") == "1"                # PRETTY=1: indent the JSON log lines for reading on a laptop


# ---------------------------------------------------------------
# STEP B. Models, reply length, and a rough price list
# ---------------------------------------------------------------

MODEL = "claude-fable-5-1"          # one model for everything: drafting, scoring chunks, token counting
MAX_TOKENS = 128000                 # the longest reply we accept: the model's hard ceiling (128K output tokens)
# The API rejects anything above 128,000 with a 400. Thinking tokens count toward this cap, so a high
# cap means a cut-off reply is next to impossible. A short answer still costs only what it uses.
# Fable 5.1 is the latest and most capable model. Thinking is always on, so part of every reply budget
# goes to thinking. It needs an account on 30-day data retention; a zero-retention org gets a 400.

# Rough list prices in USD per million tokens, used ONLY by the cameras (E7, E9) to print paise.
# Check the current price page before quoting these anywhere that matters.
PRICE_USD_PER_MTOK = {
    MODEL: {"in": 10.00, "out": 50.00},
}
INR_PER_USD = 84.0


def paise(model, input_tokens, output_tokens):
    """What one call cost, in paise, from its usage block and the price list above."""
    price = PRICE_USD_PER_MTOK.get(model, PRICE_USD_PER_MTOK[MODEL])
    usd = input_tokens / 1e6 * price["in"] + output_tokens / 1e6 * price["out"]
    return round(usd * INR_PER_USD * 100)


# ---------------------------------------------------------------
# STEP C. The inputs, read from the data/ folder
# ---------------------------------------------------------------

DATA = Path(__file__).with_name("data")
SOP_PATH = DATA / "sop_214.md"
SOP = SOP_PATH.read_text(encoding="utf-8")                           # E1 resource, E4, E5, E6, E9
ALL9 = json.loads((DATA / "tools_all9.json").read_text(encoding="utf-8"))   # the proud new belt: 9 schemas
LOGDAY = DATA / "logday.jsonl"                                       # written by gen_logday.py (E7)

CORE3 = {"get_shipment_status", "find_alternate_carriers", "process_refund"}   # what the logs say was used


# ---------------------------------------------------------------
# STEP D. Tool descriptions, picked out of the belt by name.
#         A schema is a phone-book entry: name, what it does, what input it needs. It is NOT the code.
# ---------------------------------------------------------------

def tool_schema(name):
    for tool in ALL9:
        if tool["name"] == name:
            return tool
    raise KeyError("no tool called " + name + " in tools_all9.json")


def belt(names):
    """The subset of the nine schemas with these names, in belt order."""
    return [tool for tool in ALL9 if tool["name"] in set(names)]


# ---------------------------------------------------------------
# STEP E. The tools themselves. Plain Python. The model never sees this code.
#         In production these would query the TMS, the GST portal, or the MCP server.
# ---------------------------------------------------------------

def fake_status(consignment_id):
    return {"id": consignment_id, "status": "CUSTOMS_HOLD", "missing": "e-way bill", "leg": "ICD Pune"}


def fake_carriers(lane):
    return ["BlueDart", "Delhivery", "Gati"]


def fake_refund(consignment_id, amount_inr, reason=""):
    return {"refunded": amount_inr, "consignment_id": consignment_id}


def fake_escalate(consignment_id, summary, urgency="normal"):
    return {"ticket": "OPS-7731", "consignment_id": consignment_id, "urgency": urgency}


# ---------------------------------------------------------------
# STEP F. Helpers every exhibit uses
# ---------------------------------------------------------------

def log_line(row):
    """Print one register row. A real log is ONE compact JSON line per event, so a grep or a log tool can
    read it. PRETTY=1 indents the same row over several lines for human eyes. The data is identical."""
    if PRETTY:
        print("  " + json.dumps(row, indent=2).replace("\n", "\n  "))
    else:
        print("  " + json.dumps(row))


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


def tool_result(tool_request, value, is_error=False):
    """Wrap a tool's answer the way the API wants it: tagged with the request id, content as text."""
    result = {
        "type": "tool_result",
        "tool_use_id": tool_request.id,
        "content": json.dumps(value),
    }
    if is_error:
        result["is_error"] = True
    return result


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
    # An explicit timeout (seconds) is required: with max_tokens this high the SDK would otherwise refuse a
    # non-streaming call ("Streaming is strongly recommended"). Ten minutes is far more than any exhibit needs.
    return anthropic.Anthropic(timeout=600.0, **_sdk_kwargs())


def ask_usage(model, question, system=None, max_tokens=MAX_TOKENS):
    """One call, text in, (text, input_tokens, output_tokens) out. No tools. Checks stop_reason first."""
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
    if reply.stop_reason == "max_tokens":
        # The reply was cut off. On current models the thinking block comes first and counts toward
        # max_tokens, so a cut-off reply can hold NO text at all. Fail loudly rather than return "".
        raise RuntimeError("Reply cut off at max_tokens=" + str(max_tokens) + " before it finished. Raise MAX_TOKENS.")
    return text_of(reply).strip(), reply.usage.input_tokens, reply.usage.output_tokens


def ask(model, question, system=None, max_tokens=MAX_TOKENS):
    """One call, text in, text out. The usage numbers are dropped; E7 and E9 use ask_usage() to keep them."""
    text, _, _ = ask_usage(model, question, system=system, max_tokens=max_tokens)
    return text


def ask_json(model, question, system=None, max_tokens=MAX_TOKENS):
    """ask(), then parse the reply as JSON. Models sometimes wrap JSON in a ```json fence; strip it."""
    raw = ask(model, question, system=system, max_tokens=max_tokens)
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:]                        # drop the opening ```json line
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]                   # drop the closing ``` line
        raw = "\n".join(lines)
    return json.loads(raw)


def count_tokens(tools=None, text="hi", system=None, model=MODEL):
    """How many input tokens a request would cost. Live: the API's own count_tokens endpoint, which is free.
    On battery: the four-characters-per-token bench, close enough to show the shape of a bill."""
    arguments = {"model": model, "messages": [{"role": "user", "content": text}]}
    if tools:
        arguments["tools"] = tools
    if system is not None:
        arguments["system"] = system
    return make_client().messages.count_tokens(**arguments).input_tokens
