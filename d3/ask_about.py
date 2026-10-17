# ask_about.py · Ask Claude questions about a saved output file, in a conversation.
#   Step 1  run an exhibit into a file:   python e7_dock_cameras.py > e7_out.txt 2>&1
#   Step 2  ask about it:                 python ask_about.py e7_out.txt
#   Type a question, read the answer, type the next one. Empty line or Ctrl+C ends it.

import sys
from common import make_client, text_of, MODEL, MAX_TOKENS

SYSTEM = ("You are helping a student read the output of a small Python program that calls the Claude API. "
          "Answer from the output they paste. If the output does not contain the answer, say so plainly. "
          "Be concrete: quote the line you are reading from.")


def read_text(path):
    """Read the file whatever Windows wrote it as. PowerShell 5's > saves UTF-16 (it starts with the bytes
    FF FE); PowerShell 7, cmd and Linux save UTF-8. Look at the first bytes and decode accordingly."""
    raw = open(path, "rb").read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")   # utf-8-sig also drops a UTF-8 byte-order mark


def main(path):
    output = read_text(path)
    client = make_client()
    # The output goes in ONCE, as the first user turn. Every question after that rides on the same history,
    # so the model remembers both the output and its own earlier answers.
    history = [{"role": "user", "content": "Here is the program output I want to ask about:\n\n" + output},
               {"role": "assistant", "content": "I have read the output. Ask me anything about it."}]
    print("Loaded " + path + " (" + format(len(output), ",") + " characters). Ask a question; empty line to quit.")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            break
        history.append({"role": "user", "content": question})
        # Fable's safety classifiers can decline an ordinary question. fallbacks="default" tells the API to re-run
        # a declined request on the model Anthropic recommends for that category, inside the same call.
        reply = client.beta.messages.create(model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM, messages=history,
                                            betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        if reply.stop_reason == "refusal":
            details = getattr(reply, "stop_details", None)
            why = (" category=" + str(details.category) + " · " + str(details.explanation)) if details else ""
            print("Claude: (declined to answer, and so did the fallback model." + why + ")")
            history.pop()                                   # keep the history clean for the next question
            continue
        answer = text_of(reply).strip()
        if not answer:
            print("Claude: (the reply had no text; stop_reason=" + str(reply.stop_reason) + ")")
            history.pop()
            continue
        if reply.model != MODEL:
            print("  [answered by " + reply.model + " after " + MODEL + " declined]")
        history.append({"role": "assistant", "content": answer})
        print("\nClaude: " + answer)
        print("  [" + str(reply.usage.input_tokens) + " in, " + str(reply.usage.output_tokens) + " out]")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out.txt")
