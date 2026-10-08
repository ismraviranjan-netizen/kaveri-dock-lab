# D4 · The Weighbridge — practice folder

CCAR-P Domain 4 · Evaluation, Testing & Optimization · objectives 4.1–4.6 (~10 of 63 items).
Everything in this folder is built from `CCAR-P_D4_The_Weighbridge.pdf` (the Set, Book II).
The eight exhibits are transcribed line-for-line from the PDF, so every "Lines 14–16" in a
Decode or a round points at the same line here. All eight print the PDF's captured output
to the digit — `python check.py` proves it.

## Quick start

```bash
cd d4_weighbridge
python check.py              # all eight exhibits vs the PDF's printed output -> 8/8 PASS
python e1_scorecard.py       # run one exhibit by hand
python check.py e5           # re-weigh one exhibit after a sabotage
python gen_fixtures.py       # rebuild every data file (after sabotaging a fixture)
```

Plain Python 3.10+; no packages, no API key, no network. Every exhibit is a DRY_RUN on
recorded data, exactly as in the book. On Windows, if `₹` fails to print, run
`set PYTHONUTF8=1` first (check.py already does this for you).

## What is here

| File | Objective | What it is |
|------|-----------|------------|
| `e1_scorecard.py` | 4.1 | six bars, each with operator and owner, scored on the 200-case set · reads `runs_v1_8.json` |
| `e2_golden_set.py` | 4.2 | slice counts, escalate balance, leakage check over few-shot and corpus · reads `golden_v3.jsonl`, `fewshot_v1_9_*.jsonl`, `sop_corpus_chunks.jsonl` |
| `e3_graders.py` | 4.2 | code grader, rubric-in-code with partial credit, LLM judge with UNKNOWN · self-contained |
| `e3_graders_haiku.py` | 4.2 | E3 with the judge wired to a real Claude Haiku call (`claude-haiku-5-5`); grader lines unchanged · needs `pip install anthropic` and `ANTHROPIC_API_KEY`; `--show` prints the judge's reasoning |
| `e4_calibrate.py` | 4.2 | judge calibration: overall ≥ 90 %, per category ≥ 85 % with n ≥ 10 · reads `calib_sat_40.json`, `calib_fri_52.json` |
| `e5_duel.py` | 4.3 | the offline duel's verdict, the Thursday hole, pass@k vs pass^k · self-contained |
| `e6_interrogate.py` | 4.4 | four suspects, cheapest convicting test first · reads `friday_fixtures.json` |
| `e7_levers.py` | 4.5 | route-by-eval arithmetic and the cache minimums · self-contained |
| `e8_watchman.py` | 4.6 | canary bars, the afternoon's mean vs p95, drift alarms with owners · self-contained |
| `gen_fixtures.py` | — | rebuilds all eight data files deterministically (seed 214); shows how the PDF's numbers are constructed |
| `check.py` | — | runs every exhibit and diffs it against `expected/eN.txt` — the sabotage lab's scale |
| `expected/` | — | the printed output of each exhibit, captured from the actual run |
| `rounds.md` | — | the three rounds (R read · X exam · S sabotage) for every exhibit, with hands-on sabotage recipes and the score sheet |
| `key_sealed.md` | — | the Exhibit Key — **do not open before you have scored your rounds** |
| `canon.md` | — | chapters 1–6 in note form: the five laws, every table, every tell, the errata and DRIFT box |
| `atlas.md` | — | Atlas A1–A7 as text, with a redraw checklist for Day B |
| `memory_map.md` | — | the 25 tiles |
| `ledger.md` | — | the miss ledger (one row per miss) and the lab ledger (one row per surprise) |
| `D4_Exhibits_Explained_Line_by_Line.pdf` | — | the eight exhibits with a plain-language comment at every step, exam lines in gold, decoded output and a flowchart per exhibit — read this before running a file |
| `D4_Exhibits_Explained_Kindle.epub` | — | Kindle edition of the explained exhibits: every code line as its own card with a plain comment, 53 diagrams (pies, bars, strips, pipelines, grids, flowcharts) under the hard lines; send to your Kindle or open in any EPUB reader |
| `CCAR-P_D4_The_Weighbridge.pdf` | — | the source book |

## How to practise an exhibit (the same drill for all eight)

1. **Read the chapter** in `canon.md` (or the PDF), then open the exhibit file. Read it; do not retype it.
2. **Predict the output** before you run it. Write the numbers you expect in `ledger.md` (lab ledger).
3. **Run it**: `python e3_graders.py`. Compare with your prediction. Every surprise is a ledger row.
4. **Round R (read it)** — answer the R question in `rounds.md` from the code alone.
5. **Round X (exam stem)** — pick one option and name the family of each wrong option (SD, VG, CM, OE, TR, SF, HL).
6. **Round S (sabotage)** — first answer in your head, as the book asks. Then do it for real:
   make the one-line edit the recipe names, **write down what will print**, run `python check.py eN`,
   read the diff, then restore with `git checkout -- d4_weighbridge/<file>` (and `python gen_fixtures.py`
   if you touched a data file). Change one thing, re-weigh — that is Law 4 in your hands.
7. **Score** the three rounds on the sheet at the bottom of `rounds.md` (R and S: 1 or ½; X: 1 or 0).
   Bar: 20 of 24, and no exhibit with two misses.
8. **Only then** open `key_sealed.md`. Any miss gets a row in `ledger.md` with its family.

## The two days

- **Day A** — chapters 1–6 with their exhibits (about 3 hours), three rounds each, then score, then unseal.
  Then sit *The Gauge Book* cold (40 questions, 70 minutes) — a separate book, not in this folder.
- **Day B** — redraw Atlas A1–A7 from memory on blank paper, mark against `atlas.md`; every missing box is a
  ledger row. Then *The Gauge Sheet* flaw hunt and re-sit your Gauge Book misses. Read `memory_map.md`
  last thing on Day B and first thing in repair week.

## Notes on fidelity

- The code is the PDF's code. One deliberate addition: `e6_interrogate.py` line 27 opens the fixture with
  `encoding="utf-8"` so the `§` in the cited clauses survives on Windows. Line numbers are unchanged.
- The data files are not in the PDF (it only prints their results); `gen_fixtures.py` builds them so that
  every printed number matches: 188/200 triage, 197/200 refund, p95 at sorted position 189 = 1.6 s with
  ten slower cases, mean 0.888 s, ₹5.80 mean cost, 140/40/20 slices, 35 escalate, fs-07..09 leaked on
  Sunday, 35/38 and 43/50 agreements, 21 chunks, 4 cited clauses, 7/7 → 0/7.
- The errata on page 2 are already applied: the ₹5.80 → ₹4.10 duel row, CM = constraint missed,
  HL = human loop skipped, "thinking on", and the DRIFT page (dateless 4.6+ model IDs are fixed snapshots).
