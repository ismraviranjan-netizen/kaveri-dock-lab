# E7 · The agent loop: every stop_reason lands somewhere explicit  (objective 1.3c, the 50 percent row)
#
# A loop around messages.create that keeps going while the model asks for tools and stops when it does not.
# The field that steers it is stop_reason. BUDGET is written before the loop exists. Escalation is the floor.
#
# This version NARRATES itself. For every turn it prints: the content blocks that came back, the stop_reason and
# the branch it chose, every tool call with its input and its result, how the case file grew, tokens and seconds.
# At the end: a summary of turns, tools, stop_reasons seen and the exit taken. The loop itself is unchanged.
#
# Run on battery:  DRY_RUN=1 python e7_agent_loop.py
#                  D1_SCENARIO=default|truncate|refuse|exhaust makes the stand-in exercise each branch
# Run live:        python e7_agent_loop.py

import json
import textwrap
import time
from common import make_client, text_of, fake_status, fake_carriers, MODEL, MAX_TOKENS, TOOLS_KAVERI, DRY_RUN, SCENARIO


# ---------------------------------------------------------------
# STEP 0. Things we decide BEFORE the loop exists
# ---------------------------------------------------------------

BUDGET = 6                                # the most turns we will ever pay for. Never "while True".
TOOLS = TOOLS_KAVERI                      # the detective's toolbag: both kaveri tools
BRIEF_E7 = "Why is KF-2481 stuck, and what are our options?"
WIDTH = 100                               # wrap width for printed text

# Every value stop_reason can take, what it means, and what THIS loop does about it. Printed as a legend
# before the loop runs, so the branches you do not see fire today are still in front of you.
STOP_REASONS = {
    "tool_use":    ("the model wants a tool run before it can go on",      "run every tool it asked for, send the results back, loop"),
    "end_turn":    ("the model finished its answer",                        "return the text: the natural exit"),
    "max_tokens":  ("the reply hit max_tokens before it finished",          "keep the partial text, append 'Continue.', loop"),
    "pause_turn":  ("a server-side tool paused the turn",                   "send the reply back unchanged to resume, loop"),
    "refusal":     ("the model or a safety classifier declined",            "ESCALATE with the reason, never a blind retry"),
    "<other>":     ("stop_sequence, or a value that does not exist yet",    "ESCALATE with the value, never swallow it"),
}


# ---------------------------------------------------------------
# STEP 1. The tools, dispatched by name. Plain Python.
#         An unknown tool returns a structured error, not an exception: the model can read it and adapt.
# ---------------------------------------------------------------

def run_tool(tool_request):
    if tool_request.name == "get_shipment_status":
        return fake_status(tool_request.input["consignment_id"])
    if tool_request.name == "find_alternate_carriers":
        return fake_carriers(tool_request.input["lane"])
    return {"error": "unknown tool " + tool_request.name}


# ---------------------------------------------------------------
# STEP 2. The floor. When the loop cannot finish, a human gets the case WITH a reason.
# ---------------------------------------------------------------

def escalate(reason):
    return "ESCALATED to Meera's desk (" + reason + "): " + BRIEF_E7


# ---------------------------------------------------------------
# STEP 3. Narration helpers. They only print; the loop would run the same without them.
# ---------------------------------------------------------------

def say(label, text="", indent="      "):
    """A short label, then the text wrapped under it. Empty text prints the label alone."""
    print("    " + label)
    for paragraph in str(text).strip().split("\n"):
        if paragraph.strip():
            print(textwrap.fill(paragraph, WIDTH, initial_indent=indent, subsequent_indent=indent))


def describe_blocks(reply):
    """What came back in content, block by block. Never read content[0] blind: thinking may come first."""
    parts = []
    for block in reply.content:
        if block.type == "text":
            parts.append("text(" + str(len(block.text.split())) + " words)")
        elif block.type == "tool_use":
            parts.append("tool_use(" + block.name + ")")
        elif block.type == "thinking":
            shown = getattr(block, "thinking", "") or ""
            parts.append("thinking(" + ("hidden" if not shown else str(len(shown.split())) + " words") + ")")
        else:
            parts.append(block.type)
    return ", ".join(parts) if parts else "(no content blocks)"


def print_legend():
    print()
    print("=== THE SIX WAYS A TURN CAN END, AND WHERE EACH ONE LANDS ===")
    for value, (meaning, action) in STOP_REASONS.items():
        print("  " + value.ljust(12) + meaning.ljust(58) + "-> " + action)
    print()
    print("=== BEFORE THE LOOP: the things decided in code ===")
    print("  BUDGET      " + str(BUDGET) + " turns, then escalate. Never 'while True'.")
    print("  TOOLS       " + ", ".join(t["name"] for t in TOOLS) + "  (the model may ASK; the code RUNS)")
    print("  BRIEF       " + BRIEF_E7)
    print("  max_tokens  " + str(MAX_TOKENS) + "  (thinking counts toward it)")


def print_summary(log, exit_reason, final_text):
    print()
    print("=== SUMMARY ===")
    print("  turn  stop_reason  branch taken                  tools run                     tokens in/out   seconds")
    for row in log:
        print("  " + str(row["turn"]).ljust(6) + row["stop"].ljust(13) + row["branch"].ljust(30)
              + (", ".join(row["tools"]) or "-").ljust(30) + (str(row["in"]) + "/" + str(row["out"])).ljust(16) + str(row["secs"]))
    print()
    print("  turns used      : " + str(len(log)) + " of " + str(BUDGET))
    print("  tool calls      : " + str(sum(len(r["tools"]) for r in log)))
    print("  stop_reasons    : " + ", ".join(sorted(set(r["stop"] for r in log))) + "  (of the six in the legend)")
    print("  total tokens    : " + str(sum(r["in"] for r in log)) + " in, " + str(sum(r["out"] for r in log)) + " out")
    print("  exit            : " + exit_reason)
    print()
    print("=== WHAT THE DESK RECEIVES ===")
    print(textwrap.fill(final_text, WIDTH, initial_indent="  ", subsequent_indent="  ") if final_text else "  (nothing)")


# ---------------------------------------------------------------
# STEP 4. The loop. Identical in logic to the plain version; the prints are the only addition.
# ---------------------------------------------------------------

def investigate():
    client = make_client()
    conversation = [{"role": "user", "content": BRIEF_E7}]  # the case file. The API is stateless, so this IS the memory.
    text_so_far = ""                                          # text that arrived before a max_tokens cut
    log = []                                                  # one row per turn, for the summary

    print()
    print("=== THE LOOP ===")
    print("  case file starts with 1 message: the brief.")

    for turn in range(1, BUDGET + 1):                         # bounded, always
        print()
        print("--- turn " + str(turn) + " of " + str(BUDGET) + " · sending " + str(len(conversation)) + " message(s) and "
              + str(len(TOOLS)) + " tool schemas ---")
        started = time.perf_counter()
        reply = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=TOOLS,
            messages=conversation,
        )
        secs = round(time.perf_counter() - started, 2)
        tokens_in = getattr(reply.usage, "input_tokens", 0)
        tokens_out = getattr(reply.usage, "output_tokens", 0)
        row = {"turn": turn, "stop": str(reply.stop_reason), "branch": "", "tools": [], "in": tokens_in, "out": tokens_out, "secs": secs}
        log.append(row)

        say("came back      : " + describe_blocks(reply) + "  ·  " + str(tokens_in) + " in / " + str(tokens_out) + " out  ·  " + str(secs) + " s")
        say("stop_reason    : " + str(reply.stop_reason) + "  ->  " + STOP_REASONS.get(str(reply.stop_reason), STOP_REASONS["<other>"])[0])

        # Collect any text in this reply.
        text_this_turn = text_of(reply)
        if text_this_turn.strip():
            say("model text     :", text_this_turn)

        # ---- Every stop_reason value gets its own branch. No "else" that swallows. ----

        if reply.stop_reason == "tool_use":
            # The loop's fuel. Run every tool the model asked for, send all the results back.
            row["branch"] = "run tools, loop"
            conversation.append({"role": "assistant", "content": reply.content})
            results = []
            for block in reply.content:
                if block.type == "tool_use":
                    output = run_tool(block)
                    row["tools"].append(block.name)
                    say("TOOL CALL      : " + block.name + "(" + json.dumps(block.input) + ")   id=" + str(block.id))
                    say("TOOL RESULT    : " + json.dumps(output) + "   (plain Python ran this; the model only sees the JSON)")
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(output),
                    })
            conversation.append({"role": "user", "content": results})
            say("case file      : now " + str(len(conversation)) + " messages (added the assistant's request and "
                + str(len(results)) + " tool_result block(s) as one user turn)")
            continue

        if reply.stop_reason == "end_turn":
            # The natural exit. Return everything, including text saved from an earlier max_tokens cut.
            row["branch"] = "return text (exit)"
            say("branch         : end_turn is the natural exit. Returning " + str(len((text_so_far + text_this_turn).split())) + " words.")
            print_summary(log, "end_turn on turn " + str(turn), text_so_far + text_this_turn)
            return text_so_far + text_this_turn

        if reply.stop_reason == "max_tokens":
            # Truncated is not done. Keep the partial text, ask the model to continue.
            row["branch"] = "keep partial, 'Continue.'"
            text_so_far = text_so_far + text_this_turn
            conversation.append({"role": "assistant", "content": reply.content})
            conversation.append({"role": "user", "content": "Continue."})
            say("branch         : cut off at max_tokens. Kept " + str(len(text_so_far.split())) + " words so far, asked the model to continue.")
            continue

        if reply.stop_reason == "pause_turn":
            # A server-side tool paused the turn. Send the reply back as it is to resume.
            row["branch"] = "resend to resume"
            conversation.append({"role": "assistant", "content": reply.content})
            say("branch         : server-side pause. Resending the reply unchanged so the server resumes.")
            continue

        if reply.stop_reason == "refusal":
            # The model declined. A different path, never a blind retry.
            row["branch"] = "ESCALATE (refused)"
            details = getattr(reply, "stop_details", None)
            why = (" category=" + str(getattr(details, "category", None))) if details else ""
            say("branch         : refusal" + why + ". No retry. The case goes to a human with the reason.")
            final = escalate("model refused" + why)
            print_summary(log, "refusal on turn " + str(turn), final)
            return final

        # Anything else: stop_sequence, context window exceeded, a value that does not exist yet.
        row["branch"] = "ESCALATE (unhandled)"
        say("branch         : a stop_reason this loop has no branch for. Escalating rather than guessing.")
        final = escalate("unhandled stop_reason " + str(reply.stop_reason))
        print_summary(log, "unhandled stop_reason on turn " + str(turn), final)
        return final

    # The for loop ran out. The case is still open. A human takes it, with the reason.
    print()
    say("BUDGET         : " + str(BUDGET) + " turns spent and the model is still asking. The floor catches it.")
    final = escalate("budget exhausted")
    print_summary(log, "budget exhausted after " + str(BUDGET) + " turns", final)
    return final


if __name__ == "__main__":
    print("# E7 · agent loop · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL) + " · scenario=" + SCENARIO + " · BUDGET=" + str(BUDGET))
    print_legend()
    investigate()
