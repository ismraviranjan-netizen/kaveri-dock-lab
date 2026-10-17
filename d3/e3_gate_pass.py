# E3 · The gate pass: the scoped key, checked in code, between the model and the tool  (objective 3.2, Law 1)
#
#   Authentication says WHO is calling. Authorization says WHAT that caller may open.
#   The model can ASK for any tool on its belt. The CODE checks the caller's scopes before the door opens,
#   writes an audit line either way (denials included), and hands a denial back as a tool_result error.
#   Order: authorize -> audit -> tool. Always.
#
# Run on battery:  DRY_RUN=1 python e3_gate_pass.py          Run live:  python e3_gate_pass.py

import json
from common import (make_client, trace, text_of, tool_result, belt, fake_status, fake_refund, fake_escalate,
                    MODEL, MAX_TOKENS, DRY_RUN)


# ---------------------------------------------------------------
# STEP 0. The scope table. Who holds which pass, and which pass each door needs.
# ---------------------------------------------------------------

GRANTED = {                                    # the pass each caller holds
    "kavi-agent":        {"shipment:read", "order:read", "escalate:write"},
    "refund-desk":       {"refund:write", "order:read"},
    "carrier-portal-v1": {"*"},                # the 18-month-old wildcard
}
REQUIRED = {                                   # the sign on each door
    "get_shipment_status": "shipment:read",
    "process_refund":      "refund:write",
    "escalate_to_human":   "escalate:write",
}
TOOLS = belt(REQUIRED)                         # the model's belt: the three schemas, by name


# ---------------------------------------------------------------
# STEP 1. The gate, the audit line, and the door, in that order. Plain Python.
# ---------------------------------------------------------------

def authorize(caller, tool):
    need = REQUIRED[tool]                      # an unlisted door raises KeyError: a tool nobody tabled cannot be authorized
    granted = GRANTED[caller]
    if need not in granted and "*" not in granted:
        raise PermissionError(caller + " lacks " + need + " for " + tool)


def audit_log(caller, tool, decision, reason=None):
    row = {"caller": caller, "tool": tool, "decision": decision}
    if reason:
        row["reason"] = reason
    print("  audit:", json.dumps(row))


def run_tool(caller, tool, args):
    try:
        authorize(caller, tool)                # 1. authorize
        audit_log(caller, tool, "ALLOW")       # 2. audit
    except PermissionError as error:
        audit_log(caller, tool, "DENY", str(error))
        raise
    if tool == "get_shipment_status":          # 3. the door opens
        return fake_status(args["consignment_id"])
    if tool == "process_refund":
        return fake_refund(args["consignment_id"], args["amount_inr"], args.get("reason", ""))
    if tool == "escalate_to_human":
        return fake_escalate(args["consignment_id"], args["summary"], args.get("urgency", "normal"))
    return {"error": "unknown tool " + tool}


# ---------------------------------------------------------------
# STEP 2. Three callers at one door, no model involved. Then the one-line fix.
# ---------------------------------------------------------------

def attempt(caller):
    try:
        outcome = run_tool(caller, "process_refund", {"consignment_id": "KF-2481", "amount_inr": 4200})
        print(caller.ljust(18) + " -> process_refund OK " + json.dumps(outcome))
    except PermissionError as error:
        print(caller.ljust(18) + " -> process_refund PermissionError: " + str(error))


# ---------------------------------------------------------------
# STEP 3. The model at the gate. It asks for process_refund; the gate decides; the model reads the denial.
# ---------------------------------------------------------------

SYSTEM = ("You are KAVI, the Kaveri Freight dispatcher's assistant. Use the tools to act on the customer's request. "
          "If a tool is denied, do not retry it: escalate to a human with a one-line summary, then report.")

REQUEST = "Customer on KF-2481 wants a refund of 4200 INR: it has been three days late. Check the status and process the refund."


def serve(caller, request):
    client = make_client()
    conversation = [{"role": "user", "content": request}]

    for turn in range(1, 6):                                  # bounded, always
        reply = client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM, tools=TOOLS, messages=conversation,
        )
        trace(turn, reply)

        if reply.stop_reason == "tool_use":
            conversation.append({"role": "assistant", "content": reply.content})
            results = []
            for block in reply.content:
                if block.type == "tool_use":
                    try:
                        results.append(tool_result(block, run_tool(caller, block.name, block.input)))
                    except PermissionError as error:
                        # The denial goes back as a tool_result marked is_error. The model reads it and adapts.
                        results.append(tool_result(block, {"error": "denied: " + str(error)}, is_error=True))
            conversation.append({"role": "user", "content": results})
            continue

        if reply.stop_reason == "refusal":
            return "The model declined to answer."
        return text_of(reply)

    return "ESCALATED: tool budget exhausted"


if __name__ == "__main__":
    print("# E3 · gate pass · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))

    print("=== Three callers at the refund door, before the fix ===")
    for caller in ("kavi-agent", "refund-desk", "carrier-portal-v1"):
        attempt(caller)

    print()
    print("=== The fix, after the audit: one dictionary line ===")
    GRANTED["carrier-portal-v1"] = {"shipment:read"}
    attempt("carrier-portal-v1")

    print()
    print("=== The model at the gate, calling as kavi-agent ===")
    print(serve("kavi-agent", REQUEST))
