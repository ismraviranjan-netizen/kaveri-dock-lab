# E1 · Count for free, then pay once and read the meter  (objective 2.4)
#
#   count_tokens is a FREE endpoint: it tells you the input bill before you pay it. The same sentence in
#   Hinglish costs more tokens than in English, because the tokenizer was trained mostly on English.
#   Then ONE paid call, and the usage block is read like a meter: input, output, and how much of the output
#   was thinking (Fable thinks first, and thinking is billed as output).
#
# Run on battery:  DRY_RUN=1 python e1_count_then_pay.py     Run live:  python e1_count_then_pay.py

from common import make_client, create_message, count_tokens, text_of, thinking_tokens, cost_inr, served_by, MODEL, DRY_RUN

SYSTEM = "You are the Kaveri Desk assistant. Answer in one short sentence."
TEXTS = {
    "English":  "If a consignment is held at customs, check that the e-way bill was filed today. "
                "If it was not, re-file it before 6 pm.",
    "Hinglish": "Agar consignment customs pe hold hai, to check karo ki e-way bill aaj file hua ya nahi. "
                "Nahi hua to 6 baje se pehle re-file karo.",
}


def ask(text):
    return [{"role": "user", "content": text}]


if __name__ == "__main__":
    print("# E1 · count then pay · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))

    # STEP 1. Count both texts for free. Same meaning, different token bills.
    print()
    print("=== count_tokens, free ===")
    counted = {}
    for name, text in TEXTS.items():
        counted[name] = count_tokens(ask(text))
        print("  " + name.ljust(9) + ": " + str(counted[name]).rjust(4) + " tokens")
    ratio = counted["Hinglish"] / counted["English"]
    print("  Hinglish vs English on " + MODEL + ": " + format(ratio, ".2f") + "x")
    print("  count with the model you will use: tokenizers differ")

    # STEP 2. One paid call, with the system prompt included in the count so the two numbers can be compared.
    print()
    print("=== the one paid call ===")
    full = count_tokens(ask(TEXTS["English"]), system=SYSTEM)
    reply = create_message(model=MODEL, max_tokens=1024, system=SYSTEM, messages=ask(TEXTS["English"]),
                           output_config={"effort": "low"})               # short thinking, small bill
    u = reply.usage
    print("  input tokens   : " + str(u.input_tokens) + "   (count_tokens said " + str(full) + ")")
    print("  output tokens  : " + str(u.output_tokens) + ", of which thinking " + str(thinking_tokens(u)))
    print("  this call cost : Rs " + format(cost_inr(u), ".3f") + "   | stop_reason: " + str(reply.stop_reason) + served_by(reply))
    print("  answer         : " + text_of(reply))
