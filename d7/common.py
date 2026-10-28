# common.py  -  the shared desk for the Domain 7 lab (Developer Productivity: settings, permissions, debugging).
#
#   STEP A  the switch (DRY_RUN) and the optional .env loader
#   STEP B  the model and the price card
#   STEP C  helpers: make_client(), create_message(), ask_schema(), text_of(), served_by(), the running bill
#
# DRY_RUN=1  -> the scripted stand-in from standin.py: same control flow, canned answers, no network, no bill.
# unset      -> the real anthropic SDK with ANTHROPIC_API_KEY from the environment or the repo-root .env (git-ignored).

import json
import os
from pathlib import Path


# ---------------------------------------------------------------
# STEP A. The switch, and the optional .env loader
# ---------------------------------------------------------------

for env_file in (Path(__file__).with_name(".env"), Path(__file__).resolve().parent.parent / ".env"):
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line == "" or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

DRY_RUN = os.environ.get("DRY_RUN") == "1"


# ---------------------------------------------------------------
# STEP B. The model and the price card
# ---------------------------------------------------------------

MODEL = "claude-fable-5-1"          # the newest Fable. (There is no Fable 5.5.) Thinking is always on, billed as output.
MAX_TOKENS = 128000                 # the model's ceiling; a cut-off reply is next to impossible
IN_USD, OUT_USD, FX = 10 / 1e6, 50 / 1e6, 88.0


# ---------------------------------------------------------------
# STEP C. Helpers
# ---------------------------------------------------------------

def _sdk_kwargs():
    workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    return {"default_headers": {"anthropic-workspace-id": workspace}} if workspace else {}


def make_client():
    if DRY_RUN:
        from standin import FakeClient
        return FakeClient()
    import anthropic
    return anthropic.Anthropic(timeout=600.0, **_sdk_kwargs())


BILL = {"calls": 0, "in": 0, "out": 0}          # the running meter, printed at the end of each exhibit


def create_message(**arguments):
    """messages.create with Fable's safety net: a classifier decline is re-run on the recommended model."""
    client = make_client()
    if DRY_RUN:
        reply = client.messages.create(**arguments)
    else:
        reply = client.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **arguments)
    BILL["calls"] += 1
    BILL["in"] += reply.usage.input_tokens
    BILL["out"] += reply.usage.output_tokens
    return reply


def text_of(reply):
    return "".join(b.text for b in reply.content if b.type == "text").strip()


def served_by(reply):
    model = getattr(reply, "model", MODEL)
    return "" if model == MODEL else "  [answered by " + str(model) + " after " + MODEL + " declined]"


def ask_schema(system, user, schema, effort="low"):
    """One call whose reply is forced into a JSON schema. Returns (dict, reply). stop_reason is checked first."""
    reply = create_message(model=MODEL, max_tokens=MAX_TOKENS, system=system,
                           messages=[{"role": "user", "content": user}],
                           output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}})
    if reply.stop_reason != "end_turn":
        raise RuntimeError("stopped: " + str(reply.stop_reason) + " - nothing to parse")
    return json.loads(text_of(reply)), reply


def print_bill():
    rupees = (BILL["in"] * IN_USD + BILL["out"] * OUT_USD) * FX
    print("  meter: " + str(BILL["calls"]) + " calls · " + format(BILL["in"], ",") + " tokens in · "
          + format(BILL["out"], ",") + " out · Rs " + format(rupees, ".2f") + ("  (battery: invented counts)" if DRY_RUN else ""))
