# d2/ — the Meter exhibits, runnable

The eight code exhibits from `CCAR-P_D2_Code_E1-E8_Fable.pdf` (E1 to E8), written as plain, step-numbered Python files in the same shape as `../d1/` and `../d3/`: one shared `common.py`, one `MODEL`, a stand-in for battery runs, and `ask_about.py` for questioning an output. Domain 2 is about the meter: tokens, cost, effort, the context window, the cache, and Skills.

## Run

```bash
pip install anthropic                 # once, for live runs

# live: ANTHROPIC_API_KEY in a .env file in the repo root (git-ignored; see ../.env.example)
cd d2
python e1_count_then_pay.py

# on battery: zero paid calls, no key needed
DRY_RUN=1 python e1_count_then_pay.py         # Linux / Mac
set DRY_RUN=1                                 # Windows Command Prompt, then: python e1_count_then_pay.py
$env:DRY_RUN = "1"                            # Windows PowerShell
```

`DRY_RUN=1` makes `make_client()` return the scripted stand-in in `standin.py`. It counts tokens at about four characters each, invents a thinking count from the effort dial, honours `cache_control` the way the API does (write once, read after, nothing under 512 tokens), returns a 400 for a manual thinking budget, and answers from a canned world. The exhibits run their real control flow; nothing leaves the machine.

## Models and prices

| Constant | Value | Used for |
|---|---|---|
| `MODEL` | `claude-fable-5-1` | every call |
| `IN_USD`, `OUT_USD` | $10, $50 per million tokens | the bills printed on screen; thinking is billed as output |
| `CACHE_WRITE`, `CACHE_READ` | 1.25x, 0.025x of the input price | E7's billed-equivalent column |
| `PRICE` | the ladder: Haiku 5.5, Sonnet 5.5, Opus 5.5, Fable 5.1 | E2 prices Fable's tokens on every rung |
| `FX` | 88 rupees per dollar | |
| `DESK_CALLS_PER_DAY` | 5,600 | E5 and E7 scale one call to a day |

The PDF's ladder used Haiku 4.5 at $1/$5; the current Haiku is 5.5 at $0.10/$0.50 for prompts up to 100K tokens, and that is what `PRICE` holds. Every `create_message()` call opts into the API's server-side fallback, so a safety-classifier decline is answered by the recommended model instead of crashing; the exhibits print `[answered by ...]` when that happens, because a swapped model changes the meter.

## The files

| File | What it is | Objective |
|---|---|---|
| `ask_about.py` | not an exhibit: a helper. Run any exhibit into a file, then `python ask_about.py e3_out.txt` and ask questions about the output | |
| `common.py` | the shared desk: the switch, `.env` loader, model, price card, `make_client`, `create_message`, `count_tokens`, `text_of`, `thinking_tokens`, `cost_inr` | |
| `standin.py` | the dry-run stand-in. Not needed to learn the patterns | |
| `e1_count_then_pay.py` | `count_tokens` is free: English against Hinglish; then one paid call read like a meter (input, output, thinking, rupees) | 2.4 |
| `e2_model_ladder.py` | the bar is written first; six golden tickets; exact, p95 and cost; Fable's tokens priced on every rung; a PASS/FAIL verdict in code | 2.1 |
| `e3_effort_dial.py` | one prompt at high, medium, low effort: output, thinking, seconds, rupees; then the probe that proves a manual `budget_tokens` is refused with a 400 | 2.1, 2.3 |
| `e4_six_zones.py` | the Desk prompt in zones with a cache breakpoint after the last static one; a JSON schema on the reply; the refund cap enforced in code because a schema cannot hold a maximum | 2.2 |
| `e5_few_shot_lab.py` | 0, 3 and 12 examples on six test tickets: accuracy against input tokens against rupees a day | 2.3 |
| `e6_growing_shift.py` | a 40-turn thread: whole-thread tokens against last-8-plus-summary, measured free with `count_tokens`; one paid call for the summary | 2.4 |
| `e7_cache_line.py` | the SOP pack cached three ways: no breakpoint, a timestamp above it, a timestamp below it; call 2's usage shows reads or writes; the daily cost of the wrong line | 2.5 |
| `e8_skill_on_demand.py` | a Skill uploaded once to the workspace, then used by id with the code execution tool; the two daily bills, pack-in-every-prompt against label-plus-manual-on-demand | 2.5 |

## Live versus battery: what to expect

- No battery output lines are recorded yet: the files were compiled and their helpers unit-tested, but not run. Run each one on battery first, then live, and compare.
- E1 live: the Hinglish count should be well above the English count on the same tokenizer; the paid call's input should match `count_tokens` plus a few tokens; thinking should be a large share of the output even at low effort.
- E2 live: with six tickets p95 is the slowest-but-one call, so a single slow call fails the bar. That is the point of writing the bar first.
- E3 live: output and seconds should fall from high to low; the probe should print HTTP 400.
- E4 live: the model may itself set `escalate=true`; the code gate sets it regardless. Cache written and read should both be 0, because the prefix is under 512 tokens.
- E7 live: A reads nothing; B writes on both calls because the timestamp changes the prefix; C writes once and reads on call 2. The gap line is the daily price of that one misplaced line.
- E8 live: needs the Skills API on your account. The first run uploads the Skill; later runs find it by name. On battery the stand-in returns a canned answer and a fake skill id.
- E6 and E7 make repeated calls: about 10 and 6 respectively. E5 makes 18. Nothing here is expensive, but E5 is the one to watch.

## Reading order for the exam

E1 teaches the meter. E2 and E3 are the two dials you turn before touching a prompt: which model, how much thinking. E4 and E5 are what goes in the prompt and what it costs per call. E6 and E7 are the two ways a bill grows without anyone noticing: the thread and the cache line. E8 is the way to stop paying for the manual on every call.
