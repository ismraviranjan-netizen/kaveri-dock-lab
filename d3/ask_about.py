# ask_about.py · Ask Claude questions about a saved output file, in a conversation.
#   Step 1  run an exhibit into a file:   python e7_dock_cameras.py > e7_out.txt 2>&1
#   Step 2  ask about it:                 python ask_about.py e7_out.txt
#   Type a question, read the answer, type the next one. Empty line or Ctrl+C ends it.

import sys
from common import make_client, text_of, MODEL, MAX_TOKENS

SYSTEM = ("You are helping a student read the output of a small Python program that calls the Claude API. "
          "Answer from the output they paste. If the output does not contain the answer, say so plainly. "
          "Be concrete: quote the line you are reading from.")


def main(path):
    output = open(path, encoding="utf-8").read()
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
        reply = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM, messages=history)
        if reply.stop_reason == "refusal":
            print("Claude: (declined to answer)")
            history.pop()                                   # keep the history clean for the next question
            continue
        answer = text_of(reply).strip()
        history.append({"role": "assistant", "content": answer})
        print("\nClaude: " + answer)
        print("  [" + str(reply.usage.input_tokens) + " in, " + str(reply.usage.output_tokens) + " out]")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out.txt")
