# E8 · Two bills for the same task: the monolith, the catalogue, and the monolith done right  (objective 3.8, Law 5)
#
#   Monolithic:   every SOP and every full schema in every prompt. One turn, enormous.
#   Progressive:  the MAP first (one-line stubs, the SOP index), the TERRITORY on demand (top chunks). Plus one round-trip.
#   Small+cached: the honest monolith: a small, stable, always-used set, read from the cache at a discount.
#   The stub-vs-schema line is measured with count_tokens; the rest is arithmetic you can do in the notebook.
#
# Run on battery:  DRY_RUN=1 python e8_two_bills.py          Run live:  python e8_two_bills.py

from common import count_tokens, ALL9, DRY_RUN


# ---------------------------------------------------------------
# STEP 0. Measure the one line that is measurable: nine full schemas versus nine one-line stubs
# ---------------------------------------------------------------

def stub(tool):
    """The catalogue entry: name and one line, an empty schema. Enough to know the tool exists."""
    return {"name": tool["name"], "description": tool["description"].split(".")[0] + ".",
            "input_schema": {"type": "object", "properties": {}}}


schemas_all = count_tokens(tools=ALL9)
stubs = count_tokens(tools=[stub(t) for t in ALL9])


# ---------------------------------------------------------------
# STEP 1. The three bills
# ---------------------------------------------------------------

system = 600                       # the fixed instructions
sop_corpus = 400 * 900             # 400 SOPs x ~900 tokens, stuffed whole
question = 120
monolithic = system + sop_corpus + schemas_all + question

sop_header = 260                   # the SOP index, not the SOPs
retrieved = 20 * 180               # 20 chunks that match, fetched on demand (Anthropic's data: 20 beat 5 and 10)
progressive = stubs + sop_header + retrieved + question          # + 1 round-trip to fetch

small_corpus = 45 * 900            # the honest case: a small, stable, always-used set
cache_hit_price = 0.1              # cached reads at ~10% of the normal price
small_cached = (system + small_corpus + schemas_all) * cache_hit_price + question


if __name__ == "__main__":
    print("# E8 · two bills · " + ("DRY_RUN (4 chars per token)" if DRY_RUN else "LIVE count_tokens"))
    print("nine full schemas: " + str(schemas_all) + " tokens   nine stubs: " + str(stubs) + " tokens")
    print()
    print("monolithic  : " + format(monolithic, ",").rjust(9) + " tokens/call")
    print("progressive : " + format(progressive, ",").rjust(9) + " tokens/call + 1 round-trip")
    print("small+cached: " + format(small_cached, ",.0f").rjust(9) + " token-equivalents/call, no extra turn")
    print("gap monolithic/progressive = " + format(monolithic / progressive, ".0f") + "x")
