# d1/ — the Control Tower exhibits, runnable

The eight code exhibits from `CCAR-P_D1_Control_Tower_Brief.pdf` (E1 to E8), written as plain, step-numbered Python files so they run, print, and can be read top to bottom. One set of files, used both for the dry run and for live calls. The same files are printed, with a flowchart each, in `../D1_Live_Code_With_Flowcharts.pdf`.

## Run

```bash
pip install anthropic                 # once, for live runs

# live: ANTHROPIC_API_KEY in a .env file in the repo root (git-ignored; see ../.env.example)
cd d1
python e1_augmented_llm.py

# on battery: zero paid calls, no key needed
DRY_RUN=1 python e1_augmented_llm.py          # Linux / Mac
set DRY_RUN=1                                 # Windows Command Prompt, then: python e1_augmented_llm.py
./run_all.sh     or     run_all.bat           # all eight, then E7 under three stop_reason scenarios
```

`DRY_RUN=1` makes `make_client()` return the scripted stand-in in `standin.py`. The exhibits run their real control flow (the same `stop_reason` branches, the same replayed transcript), but every reply is canned and nothing leaves the machine.

## Models

| Constant | Model | Used for |
|---|---|---|
| `MODEL_MAIN` | `claude-sonnet-5-5` | judgement, planning, drafting, synthesis, E7's loop |
| `MODEL_SMALL` | `claude-haiku-4-5` | one-word sorts, small workers, short apologies |

Production would put refunds and planning on the Opus tier. Sonnet keeps a learning run cheap: the whole series once through costs well under half a dollar. Both constants live in `common.py`.

## The files

| File | What it is | Pattern | Objective | Law |
|---|---|---|---|---|
| `common.py` | the shared desk: switches, `.env` loader, models, inputs from `data/`, the two tool schemas, the two tool functions, `text_of`, `trace`, `make_client`, `ask`, `ask_json`, `ask_async` | | | |
| `standin.py` | the dry-run stand-in. Not needed to learn the patterns | | | |
| `e1_augmented_llm.py` | one call, one tool, at most one round-trip | augmented LLM | 1.3a | |
| `e2_chaining.py` | classify, gate, draft, in a fixed order | prompt chaining | 1.3b | 2 |
| `e3_routing.py` | a cheap nurse picks the ward, the ward picks the model | routing | 1.3b | 1, 2 |
| `e4_parallel.py` | three scouts at once; three judges vote | parallelization | 1.3b | |
| `e5_orchestrator_workers.py` | the model writes the plan, code runs the workers, synthesis closes | orchestrator-workers | 1.5 | 4 |
| `e6_evaluator_optimizer.py` | writer and editor, `MAX_ROUNDS` and `PASS` | evaluator-optimizer | 1.3b | 3 |
| `e7_agent_loop.py` | a bounded loop steered by `stop_reason`, every value explicit | agent loop | 1.3c | 3 |
| `e8_replanning.py` | E5 plus a check after every finding, capped by `MAX_NEW` | re-planning | 1.5 | 3, 4 |
| `data/` | Padma's email, the refund claim, Meera's brief | | | |

## What each file prints on battery

```
e1  # turn 1 stop_reason=tool_use (get_shipment_status) / # turn 2 stop_reason=end_turn / {"category": "customs", "urgency": "high"}
e2  Desk 1 said: 'customs' / Gate passed / Desk 2 wrote 93 words / Sabotage: Gate stopped the line: bad category: customs-ish
e3  Nurse said: 'customs' -> ward: customs -> model: claude-sonnet-5-5 / Customs ward reply / 'address' -> 'delay' on claude-haiku-4-5
e4  three scout lines / Parallel 0.2 s vs Sequential 0.6 s / Votes ['APPROVE', 'REJECT', 'APPROVE'] -> Majority APPROVE
e5  Foreman's plan (ids 1-3) / Worker 1..3 with needs / RECOMMENDATION: file the e-way bill today ...
e6  Draft 0: 142 words / Round 1 editor said: <criticism> / Round 1 revised: 93 words / Round 2 editor said: PASS
e7  tool_use (get_shipment_status) / tool_use (find_alternate_carriers) / end_turn / recommendation text
e8  Initial plan / Run 1 ... / REPLAN: dropped [3] added ['file e-way bill', 'notify Padma of revised ETA'] / Run 2, Run 4, Run 5 / grew=2, budget MAX_NEW=3 not exhausted / RECOMMENDATION
```

## E7 scenarios

`D1_SCENARIO` steers the stand-in's final reply so each branch of E7 can be watched:

| Value | What the stand-in does | Branch exercised |
|---|---|---|
| `default` | tool_use, tool_use, end_turn | the healthy trace |
| `truncate` | the final reply arrives as `max_tokens`, then completes after `Continue.` | truncated is not done |
| `refuse` | the final reply is a `refusal` with `stop_details` | a different path, no blind retry |
| `exhaust` | asks for the phone on every turn | the floor: budget exhausted, human hand-off with a reason |

## Live versus battery: what to expect

- The `stop_reason` trace should match the battery run line for line. The wording will not.
- E2 and E3 have no tool, so a live nurse will most likely say `delay`, not `customs`. The customs fact only exists where a tool supplies it (E1, E7) or the code hands it over as facts (E5, E8).
- E1 live may wrap its JSON in a code fence or add prose. E1 does not parse the answer, so nothing breaks. E5 and E8 do parse, which is why `ask_json` strips the fence.
- E7's `truncate`, `refuse` and `exhaust` scenarios exist only on battery.

## Where this departs from the book, and why

- **DRY_RUN is a stand-in, not an early return.** The book's exhibits return a canned verdict before any call. Here the dry run swaps the client, so the real control flow runs with zero paid calls. Same trick as the toy foreman in the Domain 3 `e5_hybrid.py`.
- **Model IDs** are current: `claude-sonnet-5-5` and `claude-haiku-4-5`, in one place in `common.py`.
- **No server-side fallbacks**, on purpose, so E7's `refusal` branch does what the book teaches: escalate to a human with a reason.
- **`text_of()` instead of `content[0].text`**, because current models may put a thinking block first. Assistant turns are replayed whole.
- **E8's new subtasks are proper task records** with fresh ids and empty `needs`, clipped at the cap. The book's sketch appended bare strings.
- **E5 and E8 hand the workers depot facts** (`FACTS`), so a live worker reasons over facts the code supplied instead of inventing them.
- **`max_tokens` is 2048**, because thinking tokens count toward it on current models. A reply that hits the cap raises a clear error instead of returning empty text.

## Reading order for the exam

E1 is the cell. E2, E3, E4, E6 are arrangements of the cell where code owns the path (Law 2). E7 is the one arrangement where the model owns the path, bounded by a budget and an exit (Law 3). E5 and E8 are the two levels of decomposition above chaining (Law 4). Run everything on battery once, then cover the output and predict what each file prints before running it again. Companions: `../D1_Explained_COMBINED_All_8_Parts.pdf`, `../D1_Live_Code_With_Flowcharts.pdf`, `../D1_Practice_Workbook.pdf`.
