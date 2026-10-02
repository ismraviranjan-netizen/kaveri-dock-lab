# E8 · Two bills for the same task (objective 3.8)
system      = 600          # the fixed instructions
sop_corpus  = 400 * 900    # 400 SOPs x ~900 tokens, stuffed whole
schemas_all = 1_740        # nine full tool schemas (E2's live count, ~193 each)
question    = 120
monolithic = system + sop_corpus + schemas_all + question

stubs       = 9 * 25       # nine one-line tool stubs (the catalogue)
sop_header  = 260          # the SOP index, not the SOPs
retrieved   = 20 * 180     # 20 chunks that match, fetched on demand
progressive = stubs + sop_header + retrieved + question          # + 1 round-trip to fetch

small_corpus    = 45 * 900 # the honest case: a small, stable, always-used set
cache_hit_price = 0.1      # cached reads at ~10% of the normal price
small_cached = (system + small_corpus + schemas_all) * cache_hit_price + question

print(f"monolithic  : {monolithic:,} tokens/call")
print(f"progressive : {progressive:,} tokens/call + 1 round-trip")
print(f"small+cached: {small_cached:,.0f} token-equivalents/call, no extra turn")
print(f"gap monolithic/progressive = {monolithic/progressive:.0f}x")
