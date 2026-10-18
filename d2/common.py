# common.py  -  the shared desk for the eight Domain 2 exhibits (the Meter: tokens, cost, effort, cache, skills).
#
# Every exhibit imports from here, so the things that never change live in one place:
#   STEP A  the switch (DRY_RUN) and the optional .env loader
#   STEP B  the model, the price card, the exchange rate
#   STEP C  helpers: make_client(), create_message(), count_tokens(), text_of(), thinking_tokens(), cost_inr()
#
# DRY_RUN=1  -> make_client() returns the scripted stand-in from standin.py:
#               same control flow, canned replies, counted tokens, no network, no bill.
# unset      -> the real anthropic SDK. Needs:  pip install anthropic
#               and ANTHROPIC_API_KEY in the environment, or in a .env file in the repo root (git-ignored).

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


# ---------------------------------------------------------------
# STEP B. The model, the price card, the exchange rate. Domain 2 is about the meter, so these matter.
# ---------------------------------------------------------------

MODEL = "claude-fable-5-1"          # the latest model. Thinking is always on and is billed as OUTPUT.
MAX_TOKENS = 128000                 # the model's hard ceiling (128K output tokens); thinking counts toward it
FX = 88.0                           # rupees per dollar, for the bills printed on screen

IN_USD = 10 / 1e6                   # Fable 5.1: $10 per million input tokens
OUT_USD = 50 / 1e6                  # Fable 5.1: $50 per million output tokens (thinking included)
CACHE_WRITE = 1.25                  # a 5-minute cache write costs 1.25x the input price
CACHE_READ = 0.025                  # a cache read costs 0.025x the input price ($0.25 per million tokens)

# The model ladder, $ per million tokens (input, output). Check the pricing page before quoting these.
PRICE = {
    "claude-haiku-5-5":  (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5":   (4.00, 20.00),
    "claude-fable-5-1":  (10.00, 50.00),
}

DESK_CALLS_PER_DAY = 5600           # Kaveri's number: how many Desk calls a day the bills are scaled to


# ---------------------------------------------------------------
# STEP C. Helpers every exhibit uses
# ---------------------------------------------------------------

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


FALLBACK = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
# Fable 5.1 runs safety classifiers that can decline an ordinary request (stop_reason "refusal").
# fallbacks="default" asks the API to re-run a declined request on the model Anthropic recommends for that
# category, inside the same call. The reply's .model names who answered; the exhibits print it if it changed.


def create_message(betas=(), **arguments):
    """messages.create with Fable's safety net. Extra beta flags (E8's code execution) are merged in."""
    client = make_client()
    if DRY_RUN:
        return client.messages.create(**arguments)
    flags = list(FALLBACK["betas"]) + list(betas)
    return client.beta.messages.create(betas=flags, fallbacks=FALLBACK["fallbacks"], **arguments)


def count_tokens(messages, system=None, model=MODEL):
    """How many input tokens a request would cost. Live: the API's count_tokens endpoint, which is FREE
    (limited only by requests per minute). On battery: about four characters per token."""
    arguments = {"model": model, "messages": messages}
    if system is not None:
        arguments["system"] = system
    return make_client().messages.count_tokens(**arguments).input_tokens


def text_of(reply):
    """Collect the text blocks only. Fable always thinks first: never read content[0] blind."""
    answer = ""
    for block in reply.content:
        if block.type == "text":
            answer = answer + block.text
    return answer.strip()


def thinking_tokens(usage):
    """How many of the output tokens were thinking. Read defensively: older SDKs may not carry the field."""
    details = getattr(usage, "output_tokens_details", None)
    return getattr(details, "thinking_tokens", 0) or 0 if details else 0


def cost_inr(usage, model=MODEL):
    """What one call cost in rupees: input at the input rate, output (thinking included) at the output rate,
    cache writes at 1.25x and cache reads at 0.025x of the input rate."""
    usd_in, usd_out = (p / 1e6 for p in PRICE.get(model, PRICE[MODEL]))
    written = getattr(usage, "cache_creation_input_tokens", 0) or 0
    read = getattr(usage, "cache_read_input_tokens", 0) or 0
    usd = (usage.input_tokens * usd_in + usage.output_tokens * usd_out
           + written * usd_in * CACHE_WRITE + read * usd_in * CACHE_READ)
    return usd * FX


def served_by(reply):
    """'' when Fable answered, else a note naming the fallback model that did."""
    model = getattr(reply, "model", MODEL)
    return "" if model == MODEL else "  [answered by " + str(model) + " after " + MODEL + " declined]"


if DRY_RUN:
    from standin import BadRequestError                  # the stand-in's 400, so E3's probe runs on battery too
else:
    try:
        from anthropic import BadRequestError
    except ImportError:                                  # anthropic not installed: live runs will fail later anyway
        class BadRequestError(Exception):
            status_code = 400
