# E3 · The gate pass — the scoped key, checked in code (objective 3.2)
import json

GRANTED = {                                    # the pass each caller holds
    "kavi-agent":        {"shipment:read", "order:read"},
    "refund-desk":       {"refund:write", "order:read"},
    "carrier-portal-v1": {"*"},                # the 18-month-old wildcard
}
REQUIRED = {                                   # the sign on each door
    "get_shipment_status": "shipment:read",
    "process_refund":      "refund:write",
}
TOOLS = {
    "get_shipment_status": lambda consignment_id: {"id": consignment_id, "status": "CUSTOMS_HOLD"},
    "process_refund":      lambda consignment_id, amount_inr: {"refunded": amount_inr},
}

def authorize(caller, tool):
    need, granted = REQUIRED[tool], GRANTED[caller]
    if need not in granted and "*" not in granted:
        raise PermissionError(f"{caller} lacks {need} for {tool}")

def audit_log(caller, tool, decision, reason=None):
    row = {"caller": caller, "tool": tool, "decision": decision}
    if reason: row["reason"] = reason
    print("audit:", json.dumps(row))

def run_tool(caller, tool, args):
    try:
        authorize(caller, tool)                # 1 authorize
        audit_log(caller, tool, "ALLOW")       # 2 audit
    except PermissionError as e:
        audit_log(caller, tool, "DENY", str(e))
        raise
    return TOOLS[tool](**args)                 # 3 the door opens

def attempt(caller):
    try:
        print(f"{caller:18} -> process_refund OK", run_tool(caller, "process_refund",
              {"consignment_id": "KF-2481", "amount_inr": 4200}))
    except PermissionError as e:
        print(f"{caller:18} -> process_refund PermissionError: {e}")

for caller in ("kavi-agent", "refund-desk", "carrier-portal-v1"):
    attempt(caller)
print("# the fix, after the audit: one dictionary line")
GRANTED["carrier-portal-v1"] = {"shipment:read"}
attempt("carrier-portal-v1")
