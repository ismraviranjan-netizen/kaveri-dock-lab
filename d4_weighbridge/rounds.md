# The rounds — R · read it, X · exam stem, S · sabotage

One exhibit at a time. R and S from the code, in your head first. X: pick one letter and name the
family of each wrong option. Then do the hands-on S (one edit, a written prediction, `python check.py eN`,
restore). Score on the sheet at the bottom **before** opening `key_sealed.md`.

Families: **VG** vocabulary gap · **OE** over-engineered · **TR** trade-off reversed · **CM** constraint
missed · **HL** human loop skipped · **SF** silent failure · **SD** sounds-diligent · (**OP** over-permissive).

---

## E1 · e1_scorecard.py · objective 4.1

**R · read it.** Lines 14–16: with 200 runs, which sorted position does `p95()` return — and how many
cases are slower than the number it prints?

**X · exam stem.** Kaveri's board report reads "KAVI quality 96.2 % (blended), latency 0.89 s average,
cost ₹5.80". Finance has since added a reversal bar of ≤ 2 %. Which change makes the report decision-grade?

- **A.** Weight refund exactness twice inside the blend so that finance's new concern is reflected in the single headline figure.
- **B.** Report each pan on its own row against its own pre-signed bar and owner — refund exact, triage, p95 latency, cost, reversals, safety — and drop the blend.
- **C.** Raise the blended target from 96 % to 97 % and fold the reversal rate into the blend so one number still tells the story.
- **D.** Replace the average latency with the median so that one slow afternoon cannot distort the weekly headline number.

**S · sabotage in your head.** Change line 23 to compute `first_reply_p95` with the mean. On the afternoon
E8 prints (mean 0.65 s, p95 2.3 s), what does this row print — and which family is the change?

**S · hands-on.** In `e1_scorecard.py` line 23 replace
`p95([r["latency_s"] for r in runs])` with `sum(r["latency_s"] for r in runs) / n`.
Write the new `first_reply_p95` row before you run `python check.py e1`. Restore: `git checkout -- d4_weighbridge/e1_scorecard.py`.

---

## E2 · e2_golden_set.py · objective 4.2

**R · read it.** Lines 11–12: why fingerprint lower-cased, whitespace-collapsed text instead of simply
comparing case ids?

**X · exam stem.** A team's eval score climbed from 91 % to 97 % in the week a developer "improved" the
few-shot block with three examples the model kept getting wrong. Nothing else changed. What is the most
likely explanation, and the right response?

- **A.** The examples generalised to the whole task; lock in the new version and raise the pass bar to 97 % to protect the gain.
- **B.** The judge has grown lenient on this task type; recalibrate the judge against fresh human labels before anything else.
- **C.** The evaluation set is too small to trust; double it with synthetic cases before deciding whether the gain is real.
- **D.** The three examples came from the eval set, so the score now partly measures memory; remove them, re-run, and gate on a leakage check.

**S · sabotage in your head.** Delete line 22 (the corpus check). Next week's re-index accidentally copies
the golden set's text into the RAG corpus. What happens to the score — and who notices?

**S · hands-on.** Delete line 22 of `e2_golden_set.py`. Then simulate the re-index: append fifty golden
inputs to the corpus —
```bash
python -c "import json;g=[json.loads(l) for l in open('golden_v3.jsonl',encoding='utf-8')];f=open('sop_corpus_chunks.jsonl','a',encoding='utf-8');[f.write(json.dumps({'id':'reindex-'+c['id'],'index':'sop-2026-10-04','text':c['input']},ensure_ascii=False)+'\n') for c in g[:50]]"
```
Predict the Monday lines, run `python check.py e2`. Restore: `git checkout -- d4_weighbridge/e2_golden_set.py && python gen_fixtures.py`.
Then try it the other way: keep line 22, re-run the corpus copy — who notices now?

---

## E3 · e3_graders.py · objective 4.2

**R · read it.** Line 25: what does `judge()` return when the model's last word is "Maybe" — and why is that
safer than defaulting to FAIL?

**X · exam stem.** For every exception Kaveri must grade (1) the refund decision JSON, (2) whether the reply
contains an apology and a next step, and (3) whether the reply is honest about uncertainty. Which grader
assignment fits current guidance?

- **A.** (1) an exact-match code grader; (2) rubric checks in code with partial credit; (3) an LLM judge with a specific rubric and PASS/FAIL/UNKNOWN output, calibrated on human labels first.
- **B.** One calibrated LLM judge for all three outputs, so that a single grader keeps the scoring consistent across every part of the exception.
- **C.** Human graders for all three on a weekly sample, because human grading is the highest-quality method and the stakes here are financial.
- **D.** (1) an LLM judge, since amounts need nuance; (2) and (3) exact string match against a reference reply written by Meera's team.

**S · sabotage in your head.** Delete the UNKNOWN instruction from the judge prompt (lines 17–18). What
happens on cases whose verdict needs facts the judge cannot see — and how would E4 reveal it?

**S · hands-on.** This one is a thought experiment in the book because the judge replies are recorded.
Do it anyway: on line 25 change the fallback `else "UNKNOWN"` to `else "FAIL"` and run `python check.py e3`.
The second verdict changes — that is the "hallucinated verdict" the key describes. Restore the file.

---

## E4 · e4_calibrate.py · objective 4.2

**R · read it.** Saturday prints PASS, yet four categories print UNDER-SAMPLED. What did Saturday's PASS
prove — and what did it not prove?

**X · exam stem.** A support team's LLM judge agrees with human labels on 93 % of 200 calibration replies.
Only 4 of the 200 are prompt-injection attempts; on those 4 it agreed twice. The team now wants the judge
as its safety gate. What should happen first?

- **A.** Accept the judge as it stands — 93 % overall agreement clears the usual 90 % calibration bar for production graders.
- **B.** Replace the judge with full human review of every reply, since a model can never be trusted to grade safety outcomes.
- **C.** Salt the calibration set with enough human-labelled injection attempts — at least ten — and gate on agreement within that category.
- **D.** Switch to a larger judge model, because stronger models are more resistant to the injection attempts they are grading.

**S · sabotage in your head.** Change line 7 so UNKNOWN counts as a disagreement instead of going to a
human. What does Saturday print — and what will the judge's owners be tempted to do next?

**S · hands-on.** In `e4_calibrate.py` line 8 replace the filter with `decided = rows`. Predict Saturday's
first line and the `needs_facts` row, run `python check.py e4`. Restore the file.

---

## E5 · e5_duel.py · objective 4.3

**R · read it.** Line 11: why does the "judge column only" call print SHIP to canary?

**X · exam stem.** A release gate compares champion and challenger on a 200-case set. Grader columns arrive
at different times, and the gate evaluates whatever columns exist when a developer clicks "release". A
challenger shipped on its judge column and regressed refund exactness by 3.5 points. Which change
addresses the root cause?

- **A.** Ask developers, in the release checklist, to wait until the next morning before clicking release on any challenger.
- **B.** Raise the win rule's minimum gain from 3 to 5 points, so that only clearly better challengers can ever pass the gate.
- **C.** Replace the judge with a larger model, so that its column alone can be trusted to stand for the slower graders.
- **D.** Make the gate fail closed: any expected grader column that is missing counts as a failure, so nothing ships until all are home.

**S · sabotage in your head.** Set `NOISE['refund_exact'] = 4.0` "to cut false alarms". What does the first
output line print now — and why must that number be measured rather than chosen?

**S · hands-on.** Line 3: change `"refund_exact": 0.5` to `"refund_exact": 4.0`. Predict line 1, run
`python check.py e5`, restore. Second lab: make the gate fail closed yourself — on line 11 drop `and m in b`
and watch what the Thursday call does (a KeyError is the gate refusing to ship; make it print a REJECT instead).

---

## E6 · e6_interrogate.py · objective 4.4

**R · read it.** The prompt turned out guilty. Why does the script interrogate retrieval, the model and
hallucination first?

**X · exam stem.** Overnight, a RAG assistant's policy answers become fluent, confident and wrong. Git shows
no prompt change; the release manifest names claude-sonnet-5-5 on both days; the index version moved from
sop-2026-09-20 to sop-2026-09-27. Where does a careful architect look first?

- **A.** The retrieval step: read the chunks fetched for the failing questions under the new index version and compare them with the old.
- **B.** The model: dateless model IDs track the newest weights, so the most likely cause is that the model was updated overnight.
- **C.** The sampling temperature: lower it so that the model stops improvising when it is not sure of the policy answer.
- **D.** The prompt: add "answer only from the provided documents" to the system prompt and re-run the failing questions.

**S · sabotage in your head.** Put the Haiku alias `claude-haiku-4-5` in the manifest while the receipts
record `claude-haiku-4-5-20251001`. What does `model()` print — and is it a real fault?

**S · hands-on.** Line 4: set `"model": "claude-haiku-4-5"`. In `friday_fixtures.json` replace every
`"model": "claude-sonnet-5-5"` in the receipts with `"claude-haiku-4-5-20251001"`. Predict the `model` row,
run `python check.py e6`. Restore: `git checkout -- d4_weighbridge/e6_interrogate.py && python gen_fixtures.py`.
Second lab: change one chunk's `"index"` in the fixture to `sop-2026-09-20` — which row flips, and what does 20/21 tell you?

---

## E7 · e7_levers.py · objective 4.5

**R · read it.** Lines 11–13: why does `after` fall back to `before` when `routed('easy')` is False?

**X · exam stem.** An agent sends the same 9,200-token block of tools, system prompt and policy on every
call, followed by a 1,800-token customer message. It runs on Claude Haiku 4.5. Latency and cost are both
flagged. Which single change most directly improves both?

- **A.** Move the policy text into few-shot examples, so that it is no longer counted as part of the system prompt on each call.
- **B.** Truncate the policy to its first 1,000 tokens, so that the whole prompt is short enough to process quickly on every call.
- **C.** Keep the static block first and mark it for caching — it clears Haiku 4.5's 4,096-token minimum — so hits read it at 0.1× and the first token arrives sooner.
- **D.** Send every call through the Batch API instead, which halves the price of every input and output token in the workload.

**S · sabotage in your head.** Swap the order so the 1,800-token customer message goes before the 9,200-token
block. What happens to "hit" on a real day — and which family is the change?

**S · hands-on.** The order swap is arithmetic, not code: with the varying message first, no call ever hits,
so every call is a *miss* — compute `billed_input(9200, 1800, True, False)` vs the uncached call and say the
percentage. Then a code lab: line 3, set `"haiku_easy": 0.91` — predict both of the first two lines before
`python check.py e7`. That is Law 5: green first, then the lever. Restore.

---

## E8 · e8_watchman.py · objective 4.6

**R · read it.** Output line 2: which number does the 2-second promise talk about — and how many of the 100
customers waited longer than 2 s?

**X · exam stem.** Three weeks after go-live, Kaveri's weekly report shows average first-reply time 0.8 s,
yet dispatchers complain about afternoons and two customers received late escalations. Which monitoring
change surfaces and owns the problem?

- **A.** Add a dispatcher-satisfaction survey to the weekly report so that the afternoon complaints are captured in numbers.
- **B.** Alert on p95 first-reply and p95 escalation time per hour against the 2 s and 15-minute promises, each routed to a named owner with an action.
- **C.** Raise logging verbosity so that every token of every reply is stored, ready for analysis whenever the next complaint arrives.
- **D.** Move KAVI to a larger model so that every reply is produced faster and the afternoon complaints disappear on their own.

**S · sabotage in your head.** Rewrite `drift()` to compare each day only with the day before, alarming on a
3-point one-day drop. What does this week print?

**S · hands-on.** Replace lines 20–22 with a loop over `zip(days, days[1:])` that alarms when
`y["quality"] - t["quality"] >= drop_pts`, and delete lines 23–24. Predict the output, run `python check.py e8`.
Restore. Second lab: set the canary window's `"p95_s"` to 2.1 on line 28 — what prints, and who had to attend a meeting? (Nobody.)

---

## Score your rounds before you unseal

R and S: 1 point for the idea, ½ for half of it. X: 1 or 0. **Bar: 20 of 24 — and no exhibit with two misses.**
Every miss gets a ledger row with its family before you read the key.

| Exhibit | R · read | X · exam | S · sabotage | Ledger rows |
|---------|---------|---------|-------------|-------------|
| E1 scorecard | | | | |
| E2 golden set | | | | |
| E3 graders | | | | |
| E4 calibrate | | | | |
| E5 duel | | | | |
| E6 interrogate | | | | |
| E7 levers | | | | |
| E8 watchman | | | | |
| **TOTAL** | | | | |

**SEALED · the key is in `key_sealed.md` — sit the paper cold first.**
