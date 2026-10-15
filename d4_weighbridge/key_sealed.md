# The Exhibit Key — answers to the rounds

> **SEALED.** Score all 24 rounds on the sheet in `rounds.md` first. Mark R and S generously (the idea,
> not the words); mark X strictly. Any miss goes in `ledger.md` with its family.

The "verified" lines are what the sabotaged file actually prints in this folder (run and captured).

---

### E1 · X → B
- **R.** Position ⌈0.95 × 200⌉ − 1 = **189** (zero-based) — the 190th-fastest reply. **10** cases are slower. In words: 95 % of first replies were this fast or faster.
- **X.** Each pan keeps its own bar and owner; a blend (A, C) hides a failing pan however it is weighted (**SD**); the median (D) still hides the tail — the promise is a p95 (**VG**).
- **S.** **PASS** — 0.65 ≤ 2.0 — where the truth is a FAIL (p95 2.3 s). The tail breach disappears from the gate without any error: **SF**, silent failure.
  - verified on this folder's data: `first_reply_p95     0.888   <= 2.0   PASS`

### E2 · X → D
- **R.** Pasted copies arrive under new ids (fs-07…) and with changed case and spacing, so an id check sees nothing; a fingerprint of normalised text catches all three.
- **X.** Examples the model "kept getting wrong" are almost certainly golden cases — leakage (D). Locking the gain (A) is **SD**; blaming the judge (B) misses the one clause that changed (**CM**); doubling with synthetic cases (C) is **OE** and still leaks.
- **S.** Retrieval hands KAVI the exam answers; scores inflate on exactly the cases that leaked; nothing errors and nobody is alerted — **SF**. The vault check must cover every channel: prompt, few-shot, corpus, fine-tune data.
  - verified: with line 22 gone and fifty golden inputs copied into the corpus, Monday prints `leakage: none` and `GATE OPEN`.

### E3 · X → A
- **R.** UNKNOWN. An unparseable verdict goes to a human. Defaulting to FAIL (or PASS) would silently bias the score in one direction; UNKNOWN is counted separately as coverage.
- **X.** One right answer → code; a checklist → rubric in code; judgement → calibrated judge (A). One grader for all (B) throws away determinism (**VG**); all-human (C) contradicts "avoid if possible" and volume over quality (**SD**); (D) swaps the tools (**TR**).
- **S.** The judge is forced to guess PASS or FAIL — hallucinated verdicts. In E4 the UNKNOWN count drops to 0 and disagreements rise in the `needs_facts` category.

### E4 · X → C
- **R.** It proved 92 % agreement on 38 decided replies overall. It did not prove the judge was reliable on rare failure modes: five confident-but-wrong cases cannot reveal a 30 % error rate (4/5 looked fine; the truth was 12/17).
- **X.** Four cases cannot measure a category (C). Accepting the overall figure (A) misses the clause that matters (**CM**); all-human review (B) and a bigger judge (D) are **OE** — neither measures the gap.
- **S.** 35/40 = **88 % → FAIL**. The owners will be tempted to delete the UNKNOWN escape hatch to lift the figure — and a judge forced to guess produces hallucinated verdicts. Report abstention as coverage, separately.
  - verified: `Saturday: overall 88% on 40 decided (+0 UNKNOWN -> human)  FAIL` and `needs_facts  3/5  60%  UNDER-SAMPLED`.

### E5 · X → D
- **R.** `m in b` drops every metric the challenger has not reported, so outstanding columns count as "no loss" — the gate fails open.
- **X.** The root cause is a gate that treats a missing column as a pass; failing closed fixes it in configuration (D). A checklist instruction (A) is **SD** — config beats instruction; a higher gain (B) misses the clause (**CM**); a bigger judge (C) is **OE**.
- **S.** Threshold becomes max(4.0, 1.0) = 4.0 > 3.5, so the loss is treated as noise: **SHIP to canary**. The noise floor is a measurement (three champion reruns gave ±0.5); widening it by choice hides real regressions — **SF**.
  - verified: `all columns home : SHIP to canary`

### E6 · X → A
- **R.** Each is a free or near-free read (traces, receipts, citations) that clears or convicts in minutes. Clearing them is also what makes the prompt verdict trustworthy: by the time the prompt is replayed, it is the only variable left.
- **X.** The one thing that changed is the index (A). Dateless 4.6+ IDs are fixed snapshots (B, **VG**); temperature (C) does not fix stale chunks (**CM**); an instruction patch before diagnosis (D) is **SD**.
- **S.** **GUILTY** — a false alarm: the alias and the dated snapshot are the same model under two names. Pin the dated ID in the manifest so the check compares like with like (**VG**).
  - verified: `model         GUILTY   served by ['claude-haiku-4-5-20251001']`

### E7 · X → C
- **R.** A cheaper tier is promoted only on a slice where it clears the bar. Failing-but-cheaper is not an option: green first (Law 5).
- **X.** Caching a stable prefix that clears the minimum cuts both cost and time to first token (C) — the exam guide's own sample, re-set. Few-shot (A) creates no cacheable prefix (**VG**); truncation (B) loses required policy (**CM**); Batch (D) halves cost but wrecks live latency (**TR**).
- **S.** No stable prefix survives: every call writes a new cache entry at 1.25× and none is ever read — 13,300 token-equivalents a call against 11,000 uncached, about **21 % more**. **TR**: the lever pulled backwards.

### E8 · X → B
- **R.** The **p95** (2.3 s). Six customers in a hundred — positions 95–100 — waited longer than 2 s; the mean of 0.65 s hid all six.
- **X.** Per-hour percentiles against the promises, with owners and actions (B). A survey (A) is **SD**; logging everything (C) is **OE** and decides nothing; a larger model (D) is usually slower and spends cost (**TR**).
- **S.** **Nothing.** The largest one-day drop is 0.7 points, so the 3.2-point slide is invisible — **SF**. Drift is a trend; it needs a window.
  - verified: the day-over-day version prints only the canary and afternoon lines; no ALERT.

---

**What comes next.** Sit *The Gauge Book* cold (40 questions, 70 minutes, key sealed). Then Day B: Atlas
redraw (`atlas.md`), *The Gauge Sheet* flaw hunt, and your misses. *The Gauge Walk* is the fog dictionary for
any chapter that felt fast; *The Gauge Gym* is the bench for repair week. Those are separate books.
