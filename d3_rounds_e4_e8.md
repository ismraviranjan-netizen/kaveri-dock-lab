# D3 rounds · E4–E8 — R · read it, X · exam stem, S · sabotage

Same drill as `d4_weighbridge/rounds.md`, on the Loading Dock files in `d3/`. One exhibit at a time.
R and S from the code, in your head first. X: pick one letter and name the family of each wrong option.
Then the hands-on S (one edit, a written prediction, run the file live on the laptop, restore).
Fill **Your answer** and **Marking** as you go. Score on the sheet before you open the sealed key at the bottom.

Families: **VG** vocabulary gap · **OE** over-engineered · **TR** trade-off reversed · **CM** constraint
missed · **HL** human loop skipped · **SF** silent failure · **SD** sounds-diligent · **OP** over-permissive.

> Status: question paper only. No recorded answers exist for these rounds in the practice sessions, so the
> answer and marking lines are blank. Write yours in, then mark against the key.

---

## E4 · e4_chunking.py · objective 3.5

**R · read it.** Lines 62–66: `whole()` returns True only when one chunk holds both "Step 1" and "Step 6".
SOP 214 is about 1,330 words and `BOX_WORDS` is 180. Why does the fixed cutter fail this test while the
heading cutter passes it, when the heading chunk for section 4 is *longer* than a fixed box?

Your answer:

Marking:

**X · exam stem.** Kaveri's RAG assistant answers "how do I re-file an e-way bill?" with Steps 1 and 2 and
then stops, or invents Steps 3 to 6. The index was built with a 180-word fixed-size cutter over 400 SOPs.
Which change fixes the cause rather than the symptom?

- **A.** Raise the fixed box to 400 words so that any six-step procedure is likely to fit in one box.
- **B.** Cut at the document's own seams, before each heading, and write the SOP and section label inside every chunk.
- **C.** Add a 30-word overlap between fixed boxes so that a step cut in half appears whole in the next box.
- **D.** Instruct the model to say MISSING for any step it cannot see, so the invented steps stop.

Your answer:

Marking:

**S · sabotage in your head.** Change line 64 to `if "Step 1" in chunk:`. What does the `fixed` line print
now, what does the model print from the fixed box, and which family is the change?

Your answer:

Marking:

**S · hands-on.** In `d3/e4_chunking.py` line 64 replace `if "Step 1" in chunk and "Step 6" in chunk:` with
`if "Step 1" in chunk:`. Write the three count lines before you run `python d3/e4_chunking.py` (two live
calls). Restore: `git checkout -- d3/e4_chunking.py`.

Your prediction:

Marking:

---

## E5 · e5_hybrid.py · objective 3.6 and 3.5

**R · read it.** Lines 68–74: the toy foreman skips any word with a hyphen or a digit. For the query
"e-way bill re-filing", which words does the foreman actually see, and why does that put section 3
(Padma's incident) above section 4 (the re-filing procedure) on battery?

Your answer:

Marking:

**X · exam stem.** Dispatchers search SOPs two ways: exact phrases ("e-way bill re-filing", "SOP 214 step 4")
and symptoms in a customer's words ("parcel stuck, paperwork problem"). A pure embedding index ranks the
symptom queries well but drops the exact-phrase ones. What should the architect do?

- **A.** Switch to pure keyword (BM25) search, since exact SOP phrases are what dispatchers type most.
- **B.** Fine-tune the embedding model on SOP vocabulary so that hyphenated codes embed correctly.
- **C.** Run keyword and semantic retrieval together, normalise both scores to 0..1, and fuse them with a weight tuned on logged queries.
- **D.** Ask the model to rewrite each query into the SOP's own vocabulary before the embedding lookup.

Your answer:

Marking:

**S · sabotage in your head.** Set `W_SEM = 1.0` on line 24 "because meaning matters more than spelling".
Which half of the hybrid is now silent, what happens to query 1, and which family is the change?

Your answer:

Marking:

**S · hands-on.** Line 24: `W_SEM = 1.0`. Predict the `hybrid` row for both queries before
`python d3/e5_hybrid.py` (two live foreman calls, one per query). Restore. Second lab: `W_SEM = 0.0` and
predict which query the register loses.

Your prediction:

Marking:

---

## E6 · e6_shape_router.py · objective 3.6

**R · read it.** Lines 53–57: "How many times has KF-2481 been delayed?" matches two rules. Which handler
runs, what does it print, and why is that the right order even though the answer is not the one the
question asked for?

Your answer:

Marking:

**X · exam stem.** Three question shapes reach KAVI: "Where is KF-2481?", "How many shipments ran late this
week?", "How do I re-file an e-way bill after a hold?". The team proposes one RAG pipeline for all three,
with the TMS rows and the weekly counts embedded alongside the SOPs. Which is the right design?

- **A.** Keep one RAG pipeline; it is simpler to operate and the model can read a status row as easily as an SOP.
- **B.** Route by shape in code: an id goes to a structured lookup, aggregate language to a SQL count, procedure prose to hybrid RAG, and only the last road calls the model.
- **C.** Let the model decide which backend to call by giving it the TMS, the database and the index as three tools.
- **D.** Embed the TMS rows nightly so that status questions are answered from the index without a live lookup.

Your answer:

Marking:

**S · sabotage in your head.** Swap lines 54 and 55 so the id rule comes first. What does question 3 return
now, and which family is the change? Then delete line 56 (the `.*` rule): what happens on question 4?

Your answer:

Marking:

**S · hands-on.** Swap the first two entries of `RULES`. Predict the four route lines before
`python d3/e6_shape_router.py` (one live call, the RAG road). Restore. Second lab: delete the `.*` rule and
read the traceback: name the line that fails and why `route()` returned `None`.

Your prediction:

Marking:

---

## E7 · e7_dock_cameras.py · objective 3.4

**R · read it.** Lines 81–83: with 10,000 tickets in the canned day, which sorted position does `p95()`
return, and how many tickets were slower than the number it prints? Then line 95: what does the
"the mean lied" flag actually test?

Your answer:

Marking:

**X · exam stem.** KAVI's dashboard shows "retrieve: 395 ms average", inside the 1-second budget, yet
dispatchers report afternoons when answers take two to three seconds, and nobody can say which stage was
slow for a given complaint. Which change gives both the alarm and the diagnosis?

- **A.** Lower the retrieval budget from 1 s to 500 ms so that the average has more headroom on busy afternoons.
- **B.** Log one JSON line per stage with a trace id minted once per ticket, compute p95 per stage from those lines, and alert on p95 against the budget.
- **C.** Add a second dashboard that shows the maximum latency of the day, so the worst case is visible.
- **D.** Switch the retrieval step to a faster embedding model, which removes the afternoon slowness at source.

Your answer:

Marking:

**S · sabotage in your head.** Move line 61 (`trace = uuid.uuid4().hex[:8]`) inside each stage so every
log line mints its own id. Does `digest()` still work? What is lost, and which family is the change?

Your answer:

Marking:

**S · hands-on.** Line 94: replace `p = p95(xs)` with `p = sum(xs) / len(xs)`. Predict the `retrieve` row
and whether the flag still fires, then `python d3/e7_dock_cameras.py` (one live draft call). Restore.
Second lab: on line 83 change `- 1` to `+ 1` and say what happens on a day of exactly 20 tickets.

Your prediction:

Marking:

---

## E8 · e8_two_bills.py · objective 3.8

**R · read it.** Lines 40–42: the small+cached bill multiplies `system + small_corpus + schemas_all` by 0.1
but adds `question` at full price. Why is the question excluded from the discount, and what property must
the discounted block have for the 0.1 to be real?

Your answer:

Marking:

**X · exam stem.** Every KAVI call carries 400 SOPs (about 360,000 tokens) and nine full tool schemas.
Finance wants the bill down without losing answer quality. Which design is right?

- **A.** Mark the whole 360,000-token block for prompt caching so that every call after the first reads it at a tenth of the price.
- **B.** Send one-line tool stubs and the SOP index up front, fetch the top 20 matching chunks on demand, and accept one extra round-trip.
- **C.** Cut the retrieved set from 20 chunks to 5 so that each call is smaller still.
- **D.** Move the 400 SOPs into the system prompt, which is cheaper per token than the user turn.

Your answer:

Marking:

**S · sabotage in your head.** Change line 37 to `retrieved = 5 * 180` "to save tokens". What happens to the
progressive bill and the gap, what is the cost you do not see on this screen, and which family is it?

Your answer:

Marking:

**S · hands-on.** Line 41: `cache_hit_price = 1.0` (a cache that never hits). Predict the small+cached line
before `python d3/e8_two_bills.py` (live: two free `count_tokens` calls). Restore. Then line 37 to
`5 * 180`: predict the gap and write one sentence on recall.

Your prediction:

Marking:

---

## Score your rounds before you unseal

R and S: 1 point for the idea, ½ for half of it. X: 1 or 0. **Bar: 13 of 15 — and no exhibit with two misses.**
Every miss gets a ledger row with its family in `ledger.md` before you read the key.

| Exhibit | R · read | X · exam | S · sabotage | Ledger rows |
|---------|---------|---------|-------------|-------------|
| E4 chunking | | | | |
| E5 hybrid | | | | |
| E6 shape router | | | | |
| E7 dock cameras | | | | |
| E8 two bills | | | | |
| **TOTAL** | | | | |

---
---

# SEALED · key — sit the paper cold first

## E4

**R.** The fixed cutter counts 180 words and cuts wherever the count lands, so the six steps of section 4
straddle a box boundary (box 4 holds Steps 1 and 2, the rest fall in box 5). The heading cutter cuts only
before a `#` or `##` line, so section 4 is one chunk however long it is. Length is not the test;
whether the cut falls on a seam is. Battery: `fixed 8 chunks False`, `heading 10 chunks True`.

**X. B.** A: bigger boxes still cut blind, and a longer procedure breaks again (SD). C: overlap is a dial
that repairs one torn sentence, not a torn procedure (TR, treats the symptom). D: MISSING is the right
*reader* instruction, and E4 uses it, but it leaves the retriever broken (SF made visible, not fixed).

**S.** `whole(F)` now returns True because box 4 contains "Step 1", so the line reads
`fixed : 8 chunks | full procedure in one chunk: True`. The model still prints Steps 1 and 2 and MISSING for
3 to 6, because the box did not change. The test now lies while the reader tells the truth. Family: SF.

**S hands-on.** Lines: `fixed 8 ... True`, `heading 10 ... True`, `overlap 8 ... True`. Only the first changed.

## E5

**R.** `words()` keeps "e-way", "bill", "re-filing". `toy_embed` drops "e-way" and
"re-filing" for their hyphens, so the foreman sees only "bill". Section 3 narrates Padma's incident and
mentions the bill in prose, so on the single word "bill" it scores at least as well as section 4. The
register, which keeps hyphenated words and rewards rare ones, puts section 4 first. Battery:
register-only section 4, foreman-only section 3, hybrid section 4.

**X. C.** A: wins the exact phrases and loses every symptom query (TR). B: tuning the embedder for codes
is costly and still does not give exact-match guarantees (OE). D: a query rewrite adds a model call per
search and still relies on one retriever (OE, SD).

**S.** `(1 - w_sem)` becomes 0, so the register's score is multiplied away and only the foreman decides.
Query 1 ("e-way bill re-filing") falls to the foreman-only ranking: section 3 first on battery. Query 2 is
unchanged (section 1 either way). Family: TR, one half of the hybrid thrown away in the name of the other.

**S hands-on.** With `W_SEM = 1.0` the `hybrid` row equals the `foreman only` row for both queries. With
`W_SEM = 0.0` it equals the `register only` row; the symptom query is the one the register serves worst,
because none of its words appear in the SOP's spelling.

## E6

**R.** Rule 1 (`how many|count|total`) matches first, so `sql_aggregate` runs and prints 41. The question
asked for one consignment's count and got the week's count, which is wrong, but the alternative order is
worse: the id rule would return the single TMS row (status and leg) for a *count* question, a lookup
answering an aggregate. Aggregate language is the stronger signal of shape, so it goes first. The honest
fix is a per-id count handler, not a reorder. This is the Dock Book II Q35 lesson.

**X. B.** A: one pipeline makes the model invent fluent wrong numbers for counts and stale rows for status
(SF). C: letting the model pick backends costs a call on every question, including the two that need
none, and puts a routing decision where it cannot be unit-tested (TR, HL). D: nightly embeddings of live
rows are stale by design (CM).

**S.** With the id rule first, question 3 routes to `structured_lookup` and prints
`{'status': 'CUSTOMS_HOLD', 'leg': 'ICD Pune'}`: a row for a count. Family: SF, a wrong shape served
confidently. Without the `.*` rule, question 4 matches nothing, `route()` falls off the loop and returns
`None`, and line 74 `name, answer = route(q)` raises `TypeError: cannot unpack non-iterable NoneType`.
A router needs a default road the same way E3-in-D1 needed a default ward.

**S hands-on.** Lines 1, 2 and 4 unchanged; line 3 becomes `structured_lookup <- How many times has KF-2481
been delayed?` with the TMS row. Second lab: the traceback names line 74, the unpack of `None`.

## E7

**R.** `int(0.95 * 10000) - 1` is index 9499 in the sorted list: the 9,500th smallest value. Exactly
500 tickets were slower. The flag on line 95 fires when p95 is more than four times the mean, which is a
rough test for a fat tail: a few very slow tickets hidden under a comfortable average. Battery:
`retrieve mean= 395ms p95= 2,349ms <- the mean lied`.

**X. B.** A: changing the budget changes nothing about a tail the average hides (SD). C: the maximum is one
outlier, not a promise you can hold a stage to, and it still cannot tell you *which* stage (VG, p95 vs max).
D: a model change for a problem nobody has located yet (SD, TR).

**S.** `digest()` still works, because it groups by `stage` and never reads `trace`. What is lost is the
journey: the four lines of one ticket no longer share an id, so a dispatcher's complaint cannot be followed
from route to draft. Logs survive, traces die. Family: SF, and VG if you cannot say why the id is minted
once at the door.

**S hands-on.** The `retrieve` row prints p95 equal to the mean (395 ms) and the flag goes dark: the
instrument now agrees with the lie. Second lab: on a 20-ticket day `int(0.95 * 20) + 1 = 20`, which is one
past the last index of a 20-element list: `IndexError`. The `- 1` is the fence-post.

## E8

**R.** The question changes on every call, so it can never be a cache hit; only a byte-identical prefix is
read from cache. The discounted block must be small enough to carry, stable across calls, and always used.
Change one byte in it and every call pays full price. Battery: `small+cached 4,302`.

**X. B.** A: 360,000 tokens is neither small nor always used; cached reads are still a tenth of a huge
number, and any edit to one SOP invalidates everything after it (CM, TR). C: fewer chunks cut tokens and
cut recall; Anthropic's data in the file comment says 20 beat 5 and 10 (TR). D: there is no cheaper tier
for the system prompt; tokens are tokens (VG).

**S.** Progressive drops from 4,403 to 1,703 tokens (423 + 260 + 900 + 120) and the gap rises from 82x to
about 212x. The cost not on this screen is recall: the answer draws on five chunks instead of twenty, and
the file's own comment records that twenty beat five. Family: TR, a token saving bought with answer
quality, measured on the wrong screen.

**S hands-on.** With `cache_hit_price = 1.0`: `small+cached` = 600 + 40,500 + 725 + 120 = 41,945 on battery
(live differs only by the measured schema count). With `retrieved = 5 * 180`: `progressive 1,703`,
`gap 212x`, and one sentence saying the gap grew because recall shrank.
