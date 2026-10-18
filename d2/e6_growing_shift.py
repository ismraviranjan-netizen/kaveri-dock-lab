# E6 · The growing shift: context is a budget  (objective 2.4)
#
#   One dispatcher thread, 40 turns, each carrying a carrier JSON blob. v2.3 sends the whole thread every turn
#   and the bill grows every turn. v2.4 keeps the last 8 turns plus an 80-word summary of the rest, and the bill
#   stays flat. The summary is ONE paid call; everything else is count_tokens, which is free.
#
# Run on battery:  DRY_RUN=1 python e6_growing_shift.py      Run live:  python e6_growing_shift.py

from common import create_message, count_tokens, text_of, served_by, MODEL, DRY_RUN

NOTE = " Carrier JSON: " + "{'status': 'in_transit', 'hub': 'Pune', 'eta_h': 6} " * 8
TURNS = 40
KEEP = 8                                  # v2.4 keeps this many recent user turns verbatim

history = []                              # one thread: 40 user turns, each answered "Noted."
for t in range(1, TURNS + 1):
    update = "Turn " + str(t) + ": update on KF-" + str(2400 + t) + "." + NOTE
    history += [{"role": "user", "content": update}, {"role": "assistant", "content": "Noted."}]


def upto(turn):
    """The thread as it stands when user turn `turn` arrives."""
    return history[:2 * turn - 1]


if __name__ == "__main__":
    print("# E6 · growing shift · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL) + " · " + str(TURNS) + " turns, keep " + str(KEEP))

    # STEP 1. Summarise everything older than the kept window, once. The one paid call.
    old = upto(32)[:-(2 * KEEP - 1)]
    ask = {"role": "user", "content": "Write the summary now."}
    reply = create_message(model=MODEL, max_tokens=2048, output_config={"effort": "low"},
                           system="Summarise this dispatcher thread in at most 80 words: open issues only.",
                           messages=old + [ask])
    summary = text_of(reply)
    print()
    print("=== the one paid call: the summary ===")
    print("  " + format(reply.usage.input_tokens, ",") + " tokens in, " + format(reply.usage.output_tokens, ",") + " out" + served_by(reply))
    print("  " + summary[:200].replace("\n", " "))

    # STEP 2. The meter at four points in the shift. count_tokens only: free.
    print()
    print("=== input tokens per turn: whole thread (v2.3) vs last " + str(KEEP) + " + summary (v2.4) ===")
    print("  " + "turn".rjust(4) + "v2.3 whole thread".rjust(19) + "v2.4 window + summary".rjust(24))
    for turn in (10, 20, 30, 40):
        whole = count_tokens(upto(turn))
        kept = upto(turn)[-(2 * KEEP - 1):]                     # last 8 user turns + 7 replies
        lean = count_tokens(kept, system="Summary of earlier turns: " + summary)
        print("  " + str(turn).rjust(4) + format(whole, ",").rjust(19) + format(lean, ",").rjust(24))
    print()
    print("v2.3 grows every turn; v2.4 stays flat. Context editing only clears old tool results past its")
    print("trigger (100,000 input tokens by default): the window does the daily work, not the trigger.")
