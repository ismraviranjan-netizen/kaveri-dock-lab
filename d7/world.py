# world.py  -  a simulated Claude Code workstation: Arjun's laptop on the Kaveri repo.
#
# Plain Python, no model. Everything the debug ladder and the permission grid show is COMPUTED from the data
# below: five settings layers, hooks, MCP servers, memory files, an install. Change a line here and the ladder
# and the grid change with it. This is a teaching model of Claude Code, not Claude Code itself.

# ---------------------------------------------------------------
# STEP 1. The settings layers, LOWEST precedence first. Managed settings win over everything.
# ---------------------------------------------------------------

LAYERS = [
    ("user",    "~/.claude/settings.json", {
        "model": "claude-sonnet-5-5",
        "permissions": {"allow": ["Bash(npm test)"], "ask": [], "deny": []},
        "hooks": {"PostToolUse": [{"matcher": "Edit|Write", "command": "prettier --write $FILE"}]},
    }),
    ("project", ".claude/settings.json  (committed, shared)", {
        "permissions": {"allow": ["Bash(git status)"], "ask": ["Bash(git push:*)"], "deny": []},
        "hooks": {"PreToolUse": [{"matcher": "Bash", "command": "scripts/guard.sh", "timeout": 60}]},
        "enabledMcpjsonServers": ["kaveri-tms", "carrier-portal"],
    }),
    ("local",   ".claude/settings.local.json  (git-ignored, this machine)", {
        "defaultMode": "acceptEdits",
        "permissions": {"allow": ["Bash(curl:*)"], "ask": [], "deny": []},
    }),
    ("cli",     "command line: claude --model claude-opus-5-5", {"model": "claude-opus-5-5"}),
    ("managed", r"C:\Program Files\ClaudeCode\managed-settings.json  (IT, cannot be overridden)", {
        "permissions": {"allow": [], "ask": [], "deny": ["Bash(curl:*)", "Read(./.env)"],
                        "disableBypassPermissionsMode": "disable"},
    }),
]

MANAGED_PATHS = {"macOS": "/Library/Application Support/ClaudeCode/", "Linux": "/etc/claude-code/",
                 "Windows": "C:\\Program Files\\ClaudeCode\\"}

STRAY_FILES = [(".claude/hooks.json", "a PreToolUse hook for Write, matcher 'Write'")]   # NOT a settings file

ACCOUNT = {"auth": "ANTHROPIC_API_KEY from the shell environment (Arjun's personal key)",
           "expected": "team workspace login (ant auth login, Kaveri org)"}

MCP_SERVERS = [
    ("kaveri-tms", "connected", ["get_shipment_status", "list_holds"]),
    ("carrier-portal", "failed: 401 unauthorized (CARRIER_TOKEN not set)", []),
]

MEMORY = [
    ("~/.claude/CLAUDE.md", "user memory", 410, True),
    ("./CLAUDE.md", "project memory", 1280, True),
    (".claude/rules/billing.md", "project rule", 220, True),
    ("docs/CLAUDE.md", "subfolder memory: SOP 214 rules", 900, False),     # loads only when a file under docs/ is read
]

INSTALL = {"running": "2.1.290 (npm global, first on PATH)", "also_found": "2.1.302 (native installer)", "autoupdate": "updated the native install only"}

DEBUG_LOG = [
    "[hooks] PreToolUse matcher 'Bash' -> scripts/guard.sh (from .claude/settings.json)",
    "[hooks] scripts/guard.sh started for Bash(npm test)",
    "[hooks] scripts/guard.sh timed out after 60s (no output); tool call blocked",
    "[hooks] note: guard.sh waits on a network lookup that is slow off VPN",
]


# ---------------------------------------------------------------
# STEP 2. Merging: higher layers override scalars; permission lists are combined with their source kept.
# ---------------------------------------------------------------

def effective():
    merged = {"rules": [], "hooks": [], "model": None, "defaultMode": "default", "sources": [], "bypass_disabled": False}
    for name, path, data in LAYERS:
        merged["sources"].append((name, path))
        if "model" in data:
            merged["model"] = (data["model"], name)
        if "defaultMode" in data:
            merged["defaultMode"] = data["defaultMode"]
        perms = data.get("permissions", {})
        for kind in ("allow", "ask", "deny"):
            for rule in perms.get(kind, []):
                merged["rules"].append((kind, rule, name))
        if perms.get("disableBypassPermissionsMode") == "disable":
            merged["bypass_disabled"] = True
        for event, entries in data.get("hooks", {}).items():
            for entry in entries:
                merged["hooks"].append((event, entry["matcher"], entry["command"], path))
    return merged


def rule_matches(rule, action):
    """'Bash(curl:*)' matches 'Bash(curl https://...)'; 'Bash(npm test)' matches exactly; 'Read(./.env)' exactly."""
    if rule.endswith(":*)"):
        return action.startswith(rule[:-3]) and len(action) > len(rule) - 3
    return rule == action


def decide_rules(action):
    """Rules are checked deny first, then ask, then allow. Returns (kind, rule, layer) or None."""
    rules = effective()["rules"]
    for kind in ("deny", "ask", "allow"):
        for k, rule, layer in rules:
            if k == kind and rule_matches(rule, action):
                return kind, rule, layer
    return None


# ---------------------------------------------------------------
# STEP 3. The ladder: what each rung prints on this workstation. Cheap first, heavy last.
# ---------------------------------------------------------------

def rung_status():
    e = effective()
    out = ["account     : " + ACCOUNT["auth"], "model       : " + e["model"][0] + "  (set by the " + e["model"][1] + " layer)",
           "settings    :"]
    out += ["  " + name.ljust(8) + path for name, path in e["sources"]]
    return out


def rung_hooks():
    out = ["  " + ev.ljust(12) + ("matcher " + m).ljust(20) + cmd.ljust(26) + "from " + src.split("  ")[0] for ev, m, cmd, src in effective()["hooks"]]
    out += ["! " + f + " is not a settings file: its hook (" + d + ") is NOT loaded" for f, d in STRAY_FILES]
    return out


def rung_mcp():
    out = []
    for name, status, tools in MCP_SERVERS:
        out.append(("  " if status == "connected" else "! ") + name.ljust(16) + status)
        out += ["      mcp__" + name + "__" + t for t in tools]
    return out


def rung_permissions():
    e = effective()
    out = ["  " + kind.ljust(6) + rule.ljust(22) + "(" + layer + ")" for kind, rule, layer in e["rules"]]
    for kind, rule, layer in e["rules"]:
        if kind == "allow":
            hit = decide_rules(rule.replace(":*)", " https://example.com)"))
            if hit and hit[0] == "deny":
                out.append("! " + rule + " allowed in " + layer + ", but deny " + hit[1] + " (" + hit[2] + ") wins: deny is checked first")
    out.append("  bypassPermissions: " + ("DISABLED by managed settings" if e["bypass_disabled"] else "available"))
    return out


def rung_context():
    out = []
    for path, kind, tokens, loaded in MEMORY:
        out.append(("  " if loaded else "! ") + path.ljust(26) + kind.ljust(34) + (format(tokens, ",") + " tokens" if loaded
                                                                                    else "not loaded yet: loads when Claude reads a file under docs/"))
    return out


def rung_doctor():
    return ["  install     : " + INSTALL["running"], "! also found  : " + INSTALL["also_found"] + " -- two installs on PATH",
            "! auto-update : " + INSTALL["autoupdate"] + "; the shell still starts the older one", "  settings    : all JSON files parse"]


def rung_debug():
    everything = []
    for _, fn, _ in LADDER[:-1]:
        everything += fn()
    return ["(" + str(len(everything) + len(DEBUG_LOG)) + " lines shown here; the real file runs to thousands)"] + DEBUG_LOG + everything


LADDER = [  # (command, function, the question it answers)  -- the PDF's table, cheap to heavy
    ("/status", rung_status, "Which settings sources and account are active?"),
    ("/hooks", rung_hooks, "Which hooks loaded, from which file?"),
    ("/mcp", rung_mcp, "Which servers are connected? (tools appear as mcp__server__tool)"),
    ("/permissions", rung_permissions, "Which allow / deny rules apply?"),
    ("/context", rung_context, "What memory and rules files are in the window?"),
    ("/doctor", rung_doctor, "Is the install and config healthy?"),
    ("--debug", rung_debug, "Everything above, written to ~/.claude/debug/<session-id>.txt (or /debug mid-session)"),
]
