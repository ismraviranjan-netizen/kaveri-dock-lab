# The Atlas — seven pages to redraw from memory on Day B

Each page is the whole of its idea on one sheet. Day B: redraw A1–A7 on blank paper **without looking**,
then tick every box below against your drawing. Every missing box is a ledger row.

---

## A1 — the D4 wheel

Seven stations, one direction, and a loop that never stops at go-live.

```
                         ┌───────────────────────┐
                         │ 4.1 DEFINE            │
                         │ five pans · bars      │
                         │ signed first          │
                         └───────────┬───────────┘
                 ▲                   │                   │
 ┌───────────────┴───────┐           ▼           ┌───────▼───────────────┐
 │ 4.6 MONITOR           │                       │ 4.2 BUILD             │
 │ the street · canary · │                       │ golden set v3 · 200 · │
 │ drift                 │                       │ locked                │
 └───────────────────────┘                       └───────────┬───────────┘
                 ▲          ┌─────────────────┐              │
                 │          │     LAW 1       │              ▼
 ┌───────────────┴───────┐  │ A demo is a     │  ┌───────────────────────┐
 │ 4.5 OPTIMIZE          │  │ story. An eval  │  │ 4.2 GRADE             │
 │ green first ·         │  │ is a measure-   │  │ code · rubric ·       │
 │ six levers            │  │ ment.           │  │ judge · humans        │
 └───────────────────────┘  │ every arrow is  │  └───────────┬───────────┘
                 ▲          │ a number, not   │              │
                 │          │ a mood          │              ▼
 ┌───────────────┴───────┐  └─────────────────┘  ┌───────────────────────┐
 │ 4.4 DIAGNOSE          │                       │ 4.3 COMPARE           │
 │ cheapest convicting   │◄──────────────────────┤ one change · same     │
 │ test first            │                       │ ring · rule first     │
 └───────────────────────┘                       └───────────────────────┘

   Clockwise: DEFINE → BUILD → GRADE → COMPARE → DIAGNOSE → OPTIMIZE → MONITOR
   MONITOR → BUILD: every street miss becomes a golden case (200 → 214 by Diwali).
   The wheel never stops at go-live.
```

**Checklist:** ☐ 7 stations in order DEFINE → BUILD → GRADE → COMPARE → DIAGNOSE → OPTIMIZE → MONITOR
☐ Law 1 at the hub ☐ the return arrow MONITOR → BUILD ☐ 200 → 214 ☐ each station's three-word subtitle.

---

## A2 — the metric matrix

Five pans × what, how, bar, tell.

| PAN | WHAT YOU MEASURE | HOW / GRADER | KAVERI'S BAR | THE STEM TELL |
|---|---|---|---|---|
| **ACCURACY** | triage label · refund decision · reply quality (rubric pass rate) · per-slice recall on should-escalate | exact match in code · rubric in code · calibrated judge | triage ≥ 92 % · refund exact ≥ 98 % · rubric ≥ 4.0/5, none < 3 | "accurate", "correct", "quality" |
| **LATENCY** | time to first token · end-to-end · escalation time — as percentiles, by hour | trace timestamps; nearest-rank p95/p99 | first reply p95 ≤ 2 s · escalation p95 ≤ 15 min | "slow at peak", "afternoons" |
| **COST** | ₹ per exception all-in · ₹ per resolved exception incl. rework · tokens in/out · cache-hit ratio | usage fields × rates; Cost API (daily) | ≤ ₹6 all-in (Devika) | "budget", "ceiling", "per call" |
| **SAFETY** | harmful compliance AND over-refusal · missed vs needless escalation · cap respected | adversarial slice: code checks + human transcript review | 0 failures on 20 adversarial · every refund > ₹5,000 to a human | "no incidents observed" |
| **SECURITY** | PII leaks · prompt-injection success · least-privilege violations · denied calls logged | string/PII scanners in code · tool-call audit | 0 PII leaks · injection success 0 · denials logged | "SOC 2 aligned", "best practice" |

Every row needs a number, an owner and a date before the first case runs (Law 2). A blended score across
rows is where a failing pan hides.

**Checklist:** ☐ five pans ☐ four columns ☐ all six Kaveri bars with their numbers ☐ owners: Meera (accuracy, override), Arjun (latency), Devika (cost), Sunita (safety/security) ☐ the "blend hides a pan" footer.

---

## A3 — the grader tree

One right answer → code; a checklist → rubric; judgement → a calibrated judge; humans audit.

```
WHAT ARE YOU GRADING?

 Is there exactly one right answer? ──yes──► CODE GRADER
          │                                   exact or string match · JSON schema ·
          no                                  numeric tolerance — fastest, most reliable
          ▼
 Can a checklist score it? ──────────yes──► RUBRIC IN CODE
          │                                   itemised checks · partial credit per element
          no                                  (apology? next step? no invented date?)
          ▼
 Does it need judgement — ───────────yes──► LLM JUDGE
 tone, honesty, quality?                      specific rubric · PASS / FAIL / UNKNOWN ·
                                              thinking on · outcome, not path — CALIBRATE FIRST
                                                        │
                                                        ▼
                                              CALIBRATION GATE (the Set's rule)
                                              · agreement with human labels ≥ 90 % overall
                                              · AND every category ≥ 85 % with n ≥ 10
                                              · UNKNOWN → a human; coverage reported apart

                               ┌───────────────────────────────────────┐
                               │ HUMANS: label the calibration slices ·│
                               │ take every UNKNOWN · sample the tail ·│
                               │ read transcripts — they audit the     │
                               │ graders, not the volume: "avoid if    │
                               │ possible"                             │
                               └───────────────────────────────────────┘

 Current docs: prioritize volume over quality — more auto-graded cases beat fewer hand-graded ones.
 Mixed = the grader fits the slice.
```

**Checklist:** ☐ three diamonds in order ☐ three grader boxes with their one-line descriptions ☐ the calibration gate with 90 / 85 / n ≥ 10 ☐ UNKNOWN → human as coverage ☐ the humans box off to the side ☐ "volume over quality" footer.

---

## A4 — the A/B protocol

Lab duel → canary → online A/B → feedback.

```
THE LAB · offline duel
 ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐  ┌──────────────────────┐
 │ 1 FREEZE       │─►│ 2 ONE CHANGE   │─►│ 3 k TRIALS         │─►│ 4 WIN RULE           │
 │ set v3 +       │  │ prompt v1.9    │  │ noise floor from   │  │ +3 / ≤1 / safety 0 / │
 │ holdout 50 +   │  │ only           │  │ 3 champion reruns  │  │ fail closed          │
 │ bars           │  │                │  │                    │  │                      │
 └────────────────┘  └────────────────┘  └────────────────────┘  └──────────┬───────────┘
                      only a winner leaves the lab                          │
THE STREET · live traffic                                                   ▼
 ┌────────────────┐  ┌────────────────────┐  ┌────────────────┐  ┌──────────────────────┐
 │ 5 CANARY       │─►│ 6 ONLINE A/B       │─►│ 7 DECIDE       │─►│ 8 FEED BACK          │
 │ 5 % · 48 h ·   │  │ 50/50 by exception-│  │ primary metric │  │ misses → golden set  │
 │ auto-rollback  │  │ id hash · 14 days  │  │ + guardrails   │  │                      │
 └────────────────┘  └────────────────────┘  └────────────────┘  └──────────────────────┘

 CANARY = a safety check on a release        ONLINE A/B = an experiment between variants
 small share, short window, any red bar      randomised by unit, sized and run a full weekly
 rolls back automatically — it asks "is      cycle, one primary metric plus guardrails — it
 this safe?", not "is it better?"            measures real user outcomes the lab cannot
```

**Checklist:** ☐ eight numbered boxes, four per row ☐ the lab/street split ☐ the win rule's three numbers ☐ 5 % / 48 h ☐ 50/50 by exception-id hash, 14 days ☐ the canary-vs-A/B definitions.

---

## A5 — the diagnosis matrix

Symptom → suspect → cheapest convicting test → fix. (Also previewed in Chapter 4.)

| SYMPTOM | SUSPECT | CHEAPEST CONVICTING TEST | FIX + HARDEN |
|---|---|---|---|
| Confident and wrong right after a re-index; model, prompt, latency unchanged | **RETRIEVAL** | read the chunks fetched for failing cases; check the index version | fix chunking / re-index; version the index; add golden cases |
| A rule breaks after a prompt edit — cap crossed, format wrong, policy ignored | **PROMPT** | diff versions; replay the same cases on each, one change | revert or repair; add balanced cases; structured outputs for format |
| Specifics that exist nowhere — a clause, a date, an invoice | **HALLUCINATION** | source-check every claim against the record | allow "I don't know"; quotes first; cite; restrict to provided documents |
| Easy cases pass, hard multi-step cases collapse | **MODEL — too weak** | run the failing case unchanged on a stronger tier | route that slice up (eval-justified) or decompose |
| Green in the eval, red in production | **MODEL / CONFIG MISMATCH** | diff the release manifest against the evaluated config; compare traffic mix | evaluate exactly what you ship; refresh the set from the street |
| "Nothing changed" but behaviour moved | **YOUR RELEASE** | diff manifests: index, tools, config, data — not the weights | dateless 4.6+ IDs are fixed snapshots; pin dated IDs where they exist |
| Answers cut off mid-sentence | **max_tokens** | read stop_reason == "max_tokens" | raise max_tokens or ask for brevity |

Order suspects by the cost of the test that convicts them, not by your hunch.
Contain → diagnose (one change) → harden (a gate rule + a golden case).

**Checklist:** ☐ seven rows ☐ each suspect's convicting test ☐ each fix ☐ the "cost of the test, not your hunch" footer ☐ contain → diagnose → harden.

---

## A6 — the lever map

Six levers, what each buys, and the precondition that makes it safe.

| LEVER | COST | LATENCY | QUALITY RISK | PRECONDITION / LIMIT | KAVERI'S NUMBER |
|---|---|---|---|---|---|
| **ROUTE BY EVAL** | ● | ● | ! | the cheaper tier clears the bar on THAT slice | 80 % → Haiku 4.5 (93 vs 92) · ₹5.80 → ₹4.10 |
| **PROMPT CACHING** | ● | ● | ○ | stable prefix first (tools → system → messages) · above the model minimum | 9,200-token prefix · hit bills 2,720 vs 11,000 |
| **BATCH API** | ● | ✕ | ○ | work that can wait: most done < 1 h, expires at 24 h · no streaming | nightly 200 + 50 holdout at −50 % |
| **TRIM TOKENS** | ● | ● | ! | never cut what the task needs — drop unused schemas, stale text, set max_tokens | D3 bloat audit, re-read as rupees |
| **EFFORT DIAL** | ● | ● | ! | Sonnet 5.5 yes, Haiku 4.5 no · low → max, default high · changing it re-writes the message cache | router / simple work low · hard fifth stays high |
| **STREAM · PARALLEL** | ○ | ● | ○ | buys time to first token / wall-clock only — the bill is the same | three carrier checks in one gather |

● buys it ○ no effect ✕ costs it ! can spend quality — only after the eval says the bar still holds

Law 5: read which corner the stem FIXED, then pull a lever that moves a number in the free corners — and say the number.

**Checklist:** ☐ six levers ☐ the ●/○/✕/! marks per lever ☐ each precondition ☐ each Kaveri number ☐ the Law 5 footer.

---

## A7 — lab, street and the Swiss cheese

No single layer catches everything (Anthropic, Jan 2026).

```
 a failure ──╮
             ▼
   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
   │  ○   │ │      │ │  ○   │ │      │ │  ○   │ │ ○    │
   │   ╲  │ │      │ │      │ │  ○   │ │      │ │      │
   │    ╲ │ │  ○   │ │  ○   │ │      │ │  ○   │ │      │
   │     ╲│ │   ╲  │ │      │ │      │ │      │ │  ○   │
   │  ○   │ │    ● │◄┤caught│ │  ○   │ │      │ │      │
   └──────┘ └──────┘ │ here │ └──────┘ └──────┘ └──────┘
   AUTOMATED PRODUCTION A/B TESTS   USER      TRANSCRIPT  HUMAN
   EVALS     MONITORING             FEEDBACK  REVIEW      STUDIES
   golden    p95 · ₹ ·   real       dispatcher humans     multi-rater,
   set on    override    outcomes,  flags,     read       ambiguous
   every     proxy       randomised complaints trials     tasks
   change
```

Evaluation proves a change is safe to ship (the lab). Monitoring proves the promise is kept (the street).
Each layer's misses feed the golden set.

**Checklist:** ☐ six slices in order ☐ a failure that passes one hole and is caught by the next ☐ each layer's one-line description ☐ the lab/street footer ☐ "misses feed the golden set".
