# The canon — chapters 1–6 in note form

The Set's rules in the exam's own words. Every law, bar and number from *The Adventure of the Crooked
Scale* (v1.1, re-sent 5 Oct) is reused verbatim; where the Adventure was corrected, the correction is here.

## The six objectives

| Obj. | Exam guide wording | What it really tests | Your ground | Exhibits |
|------|--------------------|----------------------|-------------|----------|
| 4.1 | Define evaluation metrics (accuracy, latency, cost, safety, security) | turning "make it good" into named, owned, percentile-shaped bars across all five families | half carried (D6 SLAs, D3 percentiles) | E1 |
| 4.2 | Design evaluation datasets and test frameworks using mixed methodologies | golden-set design, leakage, balanced slices, the grader that fits each slice, judge calibration | **new** | E2 · E3 · E4 |
| 4.3 | Conduct A/B testing and iterative improvements | one change, same ring, noise floor, pre-written win rule, offline duel vs online A/B vs canary | **new** | E5 |
| 4.4 | Diagnose system issues (prompt failure, hallucinations, model mismatch) | the cheapest convicting test first; the fix that matches the suspect | mostly new | E6 |
| 4.5 | Optimize token usage, latency, and cost-performance trade-offs | which corner is fixed, which lever moves a number, the justification sentence | half carried (CCDV-F caching, Batch) | E7 |
| 4.6 | Monitor system performance using logging and observability tools | lab vs street, alerts with owners, canary, drift, the feedback loop | carried (D3 3.4) | E8 |

**Errata (the Adventure is now v1.1).** 1 · Figure F4's cost row printed ₹4.10 for the duel; routing did
not exist until Saturday, so both prompts ran at ₹5.80. 2 · Families carry their D1 glosses: CM =
constraint missed, HL = human loop skipped. 3 · The judge "reasons first, reasoning discarded" now reads
"reasons before scoring — thinking on". 4 · DRIFT re-verified: cache reads are model-dependent, dateless
model IDs are fixed snapshots, and the effort dial is new.

## The five D4 laws

1. **A demo is a story. An eval is a measurement.**
2. **Write the pass bar before the test runs.** Number, owner, date — signed before the first case is scored (Kaveri's: Tue 29 Sep). "The team will set acceptable thresholds after reviewing the results" is the canonical **SD** corpse.
3. **The judge is a model too — calibrate it before you believe it.** Agreement with human labels on a held-out slice, overall and per category; UNKNOWNs to a human; transcripts read. A stem where a judge's score rises while a code-graded metric falls is pointing at the judge.
4. **Interrogate one suspect at a time — change one thing, re-weigh.** In the duel and in diagnosis alike. The exam calls it iterative improvement; you have called it the sabotage lab since S1.
5. **Spend where the constraint points:** the cheapest model that clears the bar, cache what repeats, batch what waits. Name the fixed corner; pull the lever that moves a number in a free corner; say the sentence — *constraint + lever + direction + number*.

## The carry-over ledger — what D4 borrows

| The fact | Where you learned it | How D4 asks about it |
|----------|----------------------|----------------------|
| Mean **310 ms** vs p95 **2,900 ms** — the mean lied | D3 Loading Dock ch. 7 (3.4) | 4.1 latency bars are percentiles; 4.6 alerts on p95 by hour |
| Logs · traces · metrics; ids never as metric labels (cardinality) | D3 camera room (3.4) | 4.6 — what to log per request, what to chart |
| Justification sentence: constraint + dial + direction + number | D3 Law (3.3) | 4.5 — every lever choice is defended this way |
| An SLA is a promise about the tail, signed by two people | D6 Law 3 (6.3) | 4.1 — a bar has a number, an owner, a date |
| Pinned model IDs; re-evaluate before any migration | D6 ch. 5 (6.5) | 4.4 model mismatch · 4.6 release manifests |
| Cache: stable prefix first; minimum length; reads ≈ 0.1× | CCDV-F Part 4 demos | 4.5 lever 2 (with today's model-by-model DRIFT) |
| Batch API −50 %, results by custom_id, random order | CCDV-F Part 4 · CCAR-F S6 | 4.5 lever 3; the nightly golden re-run |
| "Valid is not true" · sabotage one variable | CCAR-F laws-of-laws | 4.2 graders · 4.3/4.4 one change at a time |
| Value = pillar + number; every loop needs a budget and an exit | D1 Laws 5 and 3 | 4.5 cost per resolved exception; 4.6 alert actions |

**The miss families.** VG vocabulary gap · OE over-engineered · TR trade-off reversed · CM constraint
missed · HL human loop skipped · SF silent failure · SD sounds-diligent · (OP over-permissive). In D4 expect
**SD** first ("monitor closely", "add a dashboard", "review regularly"), then **TR** (spending the fixed
corner), **SF** (a gate that fails open, a mean that hides the tail) and **VG** (pass@k vs pass^k, eval
harness vs agent harness, alias vs snapshot).

---

## Chapter 1 · 4.1 Define evaluation metrics

**Good criteria, in the docs' four words:** **specific** ("accurate sentiment classification", not "good
performance"), **measurable** (numbers or well-defined scales applied consistently), **achievable** (grounded
in benchmarks, prior experiments or expert knowledge) and **relevant** (aligned with the application's
purpose). Most use cases need **multidimensional** evaluation: task fidelity, consistency, relevance and
coherence, tone and style, privacy preservation, context utilization, latency, price.

| Family | What to measure | Shape of a good bar | Kaveri |
|--------|-----------------|---------------------|--------|
| Accuracy | task fidelity per output type; per-slice rates; precision/recall on classes that matter | a rate per slice, with n | triage ≥ 92 % · refund exact ≥ 98 % · rubric ≥ 4.0/5, none < 3 |
| Latency | time to first token (TTFT) and end-to-end, by hour | a percentile + a window | first reply p95 ≤ 2 s · escalation p95 ≤ 15 min |
| Cost | ₹ per exception all-in; ₹ per *resolved* exception incl. rework; tokens; cache-hit ratio | a ceiling per unit of work | ≤ ₹6 all-in (Devika) |
| Safety | harmful compliance *and* over-refusal; missed *and* needless escalation | zero-tolerance on a named slice | 0 fails on the 20 adversarial · every refund > ₹5,000 to a human |
| Security | PII leaks · injection success · least-privilege violations · denials logged | a count that must stay zero | 0 PII leaks · injection success 0 |

**Three metric shapes the exam rewards.**
1. **Per-slice, not aggregate.** v1.9's refund exact match fell 98.5 % → 95.0 %. Slice it: of the 35 should-escalate cases, v1.8 escalated 35/35 and v1.9 only 28/35 — escalation **recall** fell to 80 %. Precision asks "of what I escalated, how much needed it?"; recall asks "of what needed it, how much did I escalate?". Bars on *both* are what balanced sets exist to measure.
2. **Percentiles, never means.** E8's afternoon prints mean 0.65 s and p95 2.3 s: six customers in a hundred waited past the promise. Latency bars name a percentile *and* a window ("p95, per hour, 06:00–22:00").
3. **Cost per resolved exception.** A failed automated triage costs about ₹30 of dispatcher time. Haiku on the easy slice: ₹3.20 + 7 % × ₹30 = ₹5.30; Sonnet on the same slice: ₹5.45 + 4 % × ₹30 = ₹6.65. Routing still wins — and the comparison would flip if Haiku's failure rate rose past about 12 %.

**TRAP · the blended score.** One "overall quality" number averages pans that trade against each other — a
failing refund pan hides inside a healthy blend (E1 prints 0.962 while the per-pan rows tell the story).
Options that re-weight the blend, raise its target, or add a new metric *into* it are all the same corpse.

| When the stem or an option says… | …it is signalling | Family |
|---|---|---|
| "overall quality score", "blended", "single KPI" | a failing pan is hiding — ask for per-pan bars | SD |
| "average response time", "mean latency" | the tail is being spent — the promise is a percentile | VG |
| "thresholds agreed after the pilot results" | the bar is unfalsifiable — Law 2 | SD |
| "exceeds industry benchmarks" | not *your* bar, not your data, not your owner | CM |
| "no harmful outputs were observed" | absence of evidence — where is the adversarial slice? | SF |
| a stem that names a ₹ ceiling, an option that measures only accuracy | the fixed corner was ignored | CM |

**When MORE metrics is right.** A new harm in the stem — a compliance boundary, a new exception type, an
injection incident — usually earns **a new pan or a new slice with its own bar**, not a tighter existing
bar. Measuring more of the right things is not over-engineering; folding them into one number is the mistake.

---

## Chapter 2 · 4.2 Datasets, frameworks, mixed methodologies

**The dataset: what goes on the weighbridge.**

| Design rule | Current guidance | Kaveri's golden set |
|---|---|---|
| Start from real failures | "20–50 simple tasks drawn from real failures is a great start"; sources: dev checks, bug tracker, support queue, user-reported failures | seeded by **40** real failures, grown to **140** replayed real exceptions |
| Mirror the real distribution, edge cases included | be task-specific; don't forget edge cases | **40** edge cases (blank dates, mixed Hindi–English, ₹4,999 vs ₹5,001) |
| Attack it on purpose | safety needs its own slice | **20** adversarial (injection in an email, PII bait, cap probes) |
| Balanced sets | test where a behaviour should occur *and* where it shouldn't | **35** should-escalate / **165** should-not |
| Unambiguous tasks | two domain experts would independently reach the same verdict | every expected decision signed off by Meera's team |
| Versioned and vaulted | isolate trials; no shared state | `golden-v3` · never in a prompt, few-shot block, corpus or fine-tune |
| Volume over quality | more auto-graded cases beat fewer hand-graded ones | **200** auto-graded, humans spent on calibration |

**Capability vs regression.** The golden set is a **regression** suite: Kaveri expects it to stay at its
bars on every change. Beside it sits a **capability** set — *the Stretch Rack*, **30** hard multi-step cases
(customs hold + refund + carrier re-book) where KAVI passes only **40 %**. Capability evals start low and are
tracked, not gated. When the Stretch Rack nears 100 % it has **saturated** — it stops teaching — so its cases
graduate into the regression suite and a harder rack is written.

**Harness vocabulary (a VG favourite).** The **agent harness** is what lets the model act — it processes
inputs and orchestrates tool calls (KAVI's loop). The **evaluation harness** runs the evals end to end —
supplies tasks, runs them, records every **transcript**, grades, aggregates. A **task** is one test with
inputs and success criteria; each attempt is a **trial**; the **outcome** is the final state in the
environment, which is not the same as what the agent *says* it did.

**TRAP · leakage — the exam paper in the student's pocket.** Any channel that carries golden text into the
model turns the score into a memory test: the system prompt, a few-shot block, the RAG corpus, fine-tuning
data. Sunday's three pasted examples (E2) are the textbook case. The score rises, nothing errors, nobody is
alerted — **SF** in a lab coat.

**Mixed methodologies: the grader fits the slice.**

| Grader | Docs' verdict | Use it for | At Kaveri |
|---|---|---|---|
| Code-based (exact/string match, schema, numeric tolerance) | fastest and most reliable, extremely scalable — lacks nuance | anything with one right answer | refund decision · triage label · PII scan · "no process_refund call on injected mail" |
| Rubric in code | (a code grader with partial credit) | checklists: present / absent | apology? next step? no invented date? |
| LLM-as-judge | fast, flexible, scalable, handles judgement — **test its reliability first, then scale** | tone, honesty, open-ended quality | reply honesty about uncertainty — the Examiner |
| Human | most flexible and high quality, but slow and expensive — **avoid if possible** | calibration labels, UNKNOWNs, tail samples, transcript review | Meera's team: 40 → 52 labels; reads transcripts weekly |

**Judge discipline, current docs.** A detailed, specific rubric; an **empirical output** (PASS/FAIL, or a 1–5
scale — not prose); a grader model run **with thinking on** so it reasons before it scores; an **UNKNOWN**
escape hatch; **partial credit** on multi-part tasks; grade the **outcome, not the path** (penalising valid
routes the designer didn't foresee makes the eval brittle); and **read the transcripts** — you won't know a
grader is working until you read many of its verdicts.

**Weighing the scale: judge calibration.** Humans label a **calibration slice** blind; the judge grades the
same items; you measure **agreement** on the cases the judge decided, and report UNKNOWNs separately as
**coverage**. The Set's rule: **overall ≥ 90 % AND every failure-mode category ≥ 85 % with n ≥ 10**; a
category with fewer than ten cases is **under-sampled** — salt it with more labelled examples before you
trust the judge on it. Re-calibrate whenever the rubric, the judge model or the task changes.

| When the stem or an option says… | …it is signalling | Family |
|---|---|---|
| "curated by the vendor's team", "representative examples" | not your traffic, not your failures | CM |
| "used the most instructive test cases as examples" | leakage | SF |
| "experts hand-grade 50 replies a week" | volume over quality — automate, spend humans on calibration | SD |
| "the judge rated 96 % acceptable" (no calibration) | Law 3 — who weighed the scale? | SD |
| "grade whether the agent called tools in the expected order" | path, not outcome — brittle | OE |
| "drop the human spot-checks so the judge can scale" | calibration and transcript review removed | HL |
| "agent harness" offered where the stem means the eval runner | two different harnesses | VG |

**When MORE evaluation is right.** A new exception type earns a slice *before* it is automated; a judge that
wobbles on a category earns more calibration cases in that category; a new attack earns adversarial cases.
The set is meant to grow — Chapter 6 feeds it from the street.

---

## Chapter 3 · 4.3 A/B testing and iterative improvement

**The offline duel — the lab's A/B.**

| Discipline | Why | Kaveri's setting |
|---|---|---|
| One change | two changes at once and the result cannot be attributed (Law 4) | v1.9 differs from v1.8 by one line |
| Same ring | same cases, graders, model, tools, day | golden-v3 (200) + a fresh holdout of **50** |
| Fresh holdout | weeks of tuning against one set overfit the prompt to it | **50** cases the champion never influenced |
| A measured noise floor | a difference smaller than run-to-run spread is not a result | 3 champion reruns: refund ±**0.5** · triage ±**0.8** · reply ±**1.5** pp |
| Trials, not one run | agents are non-deterministic | k = 3 on the decisive slices |
| Units that fit the rule | "+3" must mean something on every metric | reply quality as a **pass rate** (% scoring ≥ 4/5), not a /5 average |
| Win rule before the bell | otherwise any result can be argued into a win | **+3** pp on target · ≤ **1** pp lost elsewhere · safety **0** |
| Fail closed | a missing column is not a passing column | nothing ships while any grader column is outstanding |

**pass@k vs pass^k.** pass@k is the chance that *at least one* of k trials succeeds — it rises with k and
suits work a human can retry (a triage suggestion). pass^k is the chance that *all* k succeed — it falls with
k and is what a promise owes (an automated refund). At **90 %** per trial: pass@3 = **0.999**, pass^3 =
**0.729**. Quoting pass@k for a refund agent is a **VG** corpse.

**Online A/B — the street's experiment.** The lab cannot measure what dispatchers and customers *do*. Current
guidance: it **measures actual user outcomes** and **controls for confounds**. The rules: randomise by a
unit (exception-id hash — not by time of day, not by who volunteers), one **primary metric** named in advance
plus **guardrails** that must not worsen, a sample sized to the effect you care about, a run covering at least
a full weekly cycle, and no early stopping because the line looked good on day three.

| Pilot experiment | R1 (champion) | R2 (challenger) | Reading |
|---|---|---|---|
| Design | reply template R1 | reply template R2 — one change | 50/50 by exception-id hash · **14** days · ~**13,000** drafts per arm |
| Primary: dispatcher accepts draft without edits | **61 %** | **68 %** | **+7 pp** — well beyond noise |
| Guardrail: override proxy (24 h) | **1.0 %** | **1.1 %** | within the ≤ **2 %** bar — held |
| Guardrail: first reply p95 | **1.6 s** | **1.6 s** | held |
| Decision | | | **ship R2** · its misses join the golden set |

| | Offline duel | Canary | Online A/B |
|---|---|---|---|
| Question | is B better on fixed cases? | is this release *safe*? | is B better for real users? |
| Traffic | none — the golden set | small share (**5 %**, **48 h**) | randomised split, sized for power |
| Decides by | win rule, fail closed | any red bar → automatic rollback | primary metric + guardrails |
| Kaveri | v1.8 vs v1.9 (Thursday) | 16–18 Oct go-live | R1 vs R2 during the pilot |

**Iterative improvement — the loop, not the leap.** Read the transcripts of the failures → cluster them by
failure mode → pick the biggest cluster → change one thing → re-run the golden set and the holdout → apply the
win rule → canary → monitor → every new miss becomes a golden case. Error analysis comes first: a change aimed
at no particular cluster is a guess with a version number.

| When the stem or an option says… | …it is signalling | Family |
|---|---|---|
| "B looked better in review, so roll it out and monitor" | no ring, no rule | SD |
| "change the prompt and the model together to save an iteration" | attribution spent for speed | TR |
| "run B on this week's tickets and compare with last month" | two rings — the comparison is confounded | CM |
| "stop the test early — B is clearly ahead after two days" | peeking; the weekly cycle is unrun | SF |
| "pass@5 is 99.99 %, so refunds are safe to automate" | promises are measured with pass^k | VG |

**When MORE testing is right.** A stochastic agent earns **k trials**, not one. An offline winner that changes
what humans do earns an **online A/B** before full rollout. A challenger tuned for weeks earns a **fresh
holdout**. None of these is gold-plating; each closes a specific way the result could lie.

---

## Chapter 4 · 4.4 Diagnose system issues

**The method.** **Contain** (roll back to the champion — one command) → **reproduce** (the failing cases become
a replay set) → **read** the transcripts and traces → **rank suspects by the cost of the test that convicts
them** → change **one** variable and replay → **fix** → **harden**: a gate rule and a golden case, so the same
failure can never ship silently again.

| Symptom | Suspect | Cheapest convicting test | Fix + harden |
|---|---|---|---|
| Confident and wrong right after a re-index; model, prompt, latency unchanged | **RETRIEVAL** | read the chunks fetched for failing cases; check the index version | fix chunking / re-index; version the index; add golden cases |
| A rule breaks after a prompt edit — cap crossed, format wrong, policy ignored | **PROMPT** | diff versions; replay the same cases on each, one change | revert or repair; add balanced cases; structured outputs for format |
| Specifics that exist nowhere — a clause, a date, an invoice | **HALLUCINATION** | source-check every claim against the record | allow "I don't know"; quotes first; cite; restrict to provided documents |
| Easy cases pass, hard multi-step cases collapse | **MODEL — too weak** | run the failing case unchanged on a stronger tier | route that slice up (eval-justified) or decompose |
| Green in the eval, red in production | **MODEL / CONFIG MISMATCH** | diff the release manifest against the evaluated config; compare traffic mix | evaluate exactly what you ship; refresh the set from the street |
| "Nothing changed" but behaviour moved | **YOUR RELEASE** | diff manifests: index, tools, config, data — not the weights | dateless 4.6+ IDs are fixed snapshots; pin dated IDs where they exist |
| Answers cut off mid-sentence | **max_tokens** | read stop_reason == "max_tokens" | raise max_tokens or ask for brevity |

Order suspects by the cost of the test that convicts them, not by your hunch. Learn the rows as pairs; the
exam hands you a symptom.

**The three named suspects.**
- **Prompt failure.** Signs: a rule broken after an edit (cap crossed, format wrong, policy ignored), or instructions that conflict. Test: diff the versions and replay the same failing cases on each. Fix: repair or revert the wording, add balanced cases — and where the failure is in *format*, move it out of instructions entirely: **structured outputs** (`output_config.format` with a JSON schema) beat "please reply in JSON" (config beats instruction).
- **Hallucination.** Signs: specifics that exist nowhere. Test: source-check every claim against the record. Fixes, from the docs: **allow "I don't know"**; have the model **extract direct quotes first** and answer from them; **cite** a source for each claim and retract what has none; **restrict** answers to the provided documents; advanced: chain-of-thought verification, **best-of-N** comparison (inconsistency across samples flags invention), iterative refinement. A bigger model is not on the list.
- **Model mismatch** has three meanings — learn all three. (1) **Too weak for the task**: easy cases pass, hard multi-step cases fail; test by running the failing case unchanged on a stronger tier; fix by routing that slice up (eval-justified) or decomposing. (2) **Evaluated ≠ shipped**: the eval ran one model, prompt, index or traffic mix and production runs another; test by diffing the release manifest against the evaluated config. (3) **A model change nobody re-evaluated**: a migration done without re-sitting the golden set.

**DRIFT · model IDs are fixed snapshots.** The older reading: "a dateless model ID such as claude-sonnet-5-5
tracks the newest weights, so behaviour can change under you." Current docs (verified 5 Oct 2026): for the
4.6 generation onward the dateless ID **is** the snapshot; Anthropic does not change the weights or
configuration of an existing model ID. Older dated families keep aliases (claude-haiku-4-5 →
claude-haiku-4-5-20251001). So "the weights silently changed" is never your first suspect — it is the
distractor in the exam guide's own sample question. If behaviour moved, something in *your* release moved:
index, tools, config, data, prompt.

| When the stem or an option says… | …it is signalling | Family |
|---|---|---|
| "move to a larger model" as the first step | most expensive test, weakest conviction | OE |
| "roll back and monitor closely" — and nothing else | containment without diagnosis | SD |
| "lower the temperature" for wrong facts after a refresh | the fault is upstream of sampling | CM |
| "the model weights changed overnight" | fixed snapshots — look at your release | VG |
| "add a disclaimer that answers may be inaccurate" | labels the failure, fixes nothing | SD |
| "fine-tune on the failing cases" | a heavy fix before a cheap diagnosis | OE |

**When the expensive suspect IS guilty.** If the failing cases pass **untouched** on the stronger tier and the
task is genuinely multi-step, the model was the gap — upgrading *that slice* is the right, eval-justified
spend. **OE** is choosing the big model *first*, not choosing it *ever*.

---

## Chapter 5 · 4.5 Optimize tokens, latency, cost-performance

**Six levers (preconditions verified 5 Oct 2026).**

| Lever | Buys | Preconditions and limits | Trap |
|---|---|---|---|
| 1 Route by eval | cost, latency | promote a cheaper tier only on a slice where it clears the bar; Haiku 4.5 is the docs' pick for speed-critical work | smallest model regardless (**TR**) |
| 2 Prompt caching | cost and time to first token | prefix order tools → system → messages; a change invalidates that level and everything after; minimum **512** (Sonnet 5.5) to **4,096** (Haiku 4.5); writes **1.25×** (5-min TTL) or **2×** (1-hour); reads **0.1×** on most models (Opus 5.5 **0.05×**, Fable/Mythos 5.1 **0.025×**); TTL refreshed free on each hit; up to **4** breakpoints | caching the varying message (**TR**) · prefix under the minimum (**VG**) |
| 3 Batch API | cost only (**−50 %** on all usage) | most batches finish within an hour; they expire at **24 h**; results kept **29 days**; no streaming; stacks with caching; the docs name large-scale evaluations as a fit | batching the live 2 s replies (**CM**) |
| 4 Trim tokens | cost, latency | the docs' "optimize prompt and output length": drop unused tool schemas and stale text, ask for concision, set max_tokens — never cut what the task needs | truncating required policy (**CM**) |
| 5 Effort (new) | cost, latency — at a capability price | low · medium · high · xhigh · max; default high (Opus 5.5: medium); Sonnet 5.5 yes, Haiku 4.5 no; a behavioural signal, not a hard budget; changing it invalidates the message cache | lowering effort on the hard fifth (**TR**) |
| 6 Stream · parallelize | perceived latency / wall-clock only | streaming improves responsiveness; parallel independent calls cut elapsed time — the bill is unchanged | "parallelize to cut spend" (**TR**) |

**Measure before and after.** Every response's usage block reports `input_tokens` (after the last cache
breakpoint), `cache_creation_input_tokens`, `cache_read_input_tokens` and `output_tokens`; total input is the
sum of the first three. Count tokens with the free counting endpoint before paying for a call (your free-probe
habit). Cache-hit ratio = cache reads ÷ total input, charted daily.

**Law 5 in a sentence.** "To hold ≤ ₹6 with the 92 bar intact, route the easy 80 % to Haiku 4.5: ₹5.80 → ₹4.10."
The router itself costs ₹0.10 per exception and is counted: 0.80 × 3.20 + 0.20 × 7.20 + 0.10 = 4.10. The
900-token router prompt on Haiku 4.5 is under the 4,096 minimum: caching it would silently do nothing.

| When the stem or an option says… | …it is signalling | Family |
|---|---|---|
| "use the smallest model everywhere" / lower effort on the hard slice | the quality bar is the fixed corner | TR |
| "cache the conversation" with the customer message first | no stable prefix — every call writes, none reads | TR |
| "batch the live replies to halve cost" | the 2 s promise is the fixed corner | CM |
| "truncate the policy to speed up the prompt" | required content cut | CM |
| "parallelize to cut spend" | wall-clock only; the bill is unchanged | TR |
| a cache on a 900-token Haiku prompt | under the minimum — a no-op | VG |

**When spending MORE is right.** If the stem fixes **quality** and the system sits below the bar, the right
option may be the expensive one: the stronger tier for the hard slice, higher effort, more retrieval.
Optimization has a direction, not a religion.

---

## Chapter 6 · 4.6 Monitor with logging and observability

**Lab, street, and the layers between.** **Evaluation** runs before release on a fixed, versioned set and
proves a change is safe to ship. **Monitoring** runs after release on live traffic and proves the promise is
being kept. The full picture is a **Swiss cheese** model: automated evals, production monitoring, A/B tests,
user feedback, manual transcript review and systematic human studies each have holes; together they catch
what any one misses (Atlas A7).

| Log per request (bounded fields) | Chart on the wall (the promises) | Alert (threshold + owner + action) |
|---|---|---|
| request id · exception id (logs and traces only) | first reply **p95** per hour | p95 > **2 s** for **2** days running → Arjun · freeze releases |
| model ID that served (from the response) · prompt and index versions | escalation **p95** per hour | escalation p95 > **15 min** → Vikram · staff the queue |
| tool calls · stop_reason · latency (TTFT and total) | ₹ per exception (usage × rates; Cost API daily) | ₹ > **6** for a day → Devika · review routing mix |
| usage: input, cache write, cache read, output tokens | override proxy (human overrides within 24 h) | override > **2 %** → Meera · open transcripts |
| outcome label · override flag · redacted text only | daily quality sample (50 live replies, judged) | quality **−3 pts** over 7 days → Meera · error analysis |

**Anthropic's own instruments.** Each response carries its usage block and the model ID that served it. At
organisation level, the **Usage and Cost Admin API** reports token usage (uncached input, cached input, cache
creation, output) in **1-minute**, **1-hour** or **1-day** buckets, grouped or filtered by model, workspace,
API key and service tier; the cost endpoint reports USD at daily granularity. It needs an **Admin API key** —
workspace keys do not work — data typically lands within about **5 minutes**, and the docs suggest polling no
more than once a minute. Listed uses: cache-efficiency measurement and budget alerts.

**Cardinality, carried from D3.** Ids belong in logs and traces, never as metric labels: a label per customer
melts the metrics store. Labels are bounded categories — exception type, model, prompt version.

**The canary.** **5 %** of live traffic for **48 h** against the gate's own bars; any red bar rolls back
automatically; green promotes to **25 %**, then **100 %**. **The drift alarm** watches the slow rot no single
day shows: quality down **3 pts** over seven days, or p95 over budget two days running. **The loop**: every
street miss becomes a golden case (**200 → 214** by Diwali).

| When the stem or an option says… | …it is signalling | Family |
|---|---|---|
| "add a dashboard" | renders, does not decide — where is the threshold, owner, action? | SD |
| "record per-customer metrics" / customer id as a label | cardinality — ids belong in traces | OE |
| "the evaluation set can be retired after go-live" | monitoring complements evals; it never replaces them | SF |
| "reports shared monthly, on request" | no cadence, no owner, no trigger | SD |
| "pull org cost reports with the app's workspace key" | the Usage and Cost API needs an Admin key | VG |
| "roll out to 100 % and roll back if complaints rise" | no canary, no automatic threshold | HL |

**When MORE monitoring is right.** A new promise earns its own panel **and** its own alert; an irreversible
action earns a canary stage before full rollout; a new exception type earns a bounded metric label and a
golden slice. None of that is noise — noise is alerts nobody owns.
