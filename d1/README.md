# d1/ — the Control Tower exhibits, runnable

The eight code exhibits from `CCAR-P_D1_Control_Tower_Brief.pdf` (E1 to E8), written as standalone files so they run and print, the way the Domain 3 scripts at the repository root do. Padma's email, the refund claim and Meera's brief live in `data/`. The two kaveri tool schemas mirror `../e1_kaveri_mcp.py`.

## Run

```bash
pip install fastmcp            # not needed here; only for the D3 scripts
cd d1
DRY_RUN=1 python e1_augmented_llm.py      # any single exhibit
./run_all.sh                              # all eight, then E7 under three stop_reason scenarios
```

`DRY_RUN=1` makes `make_client()` return a scripted stand-in for the Messages API. The exhibits run their real control flow (the same `stop_reason` branches, the same replayed transcript), but every reply is canned and nothing leaves the machine. Zero paid calls, no key, no SDK needed.

For a live run: `pip install anthropic`, set `ANTHROPIC_API_KEY`, and run without `DRY_RUN`. The live path is written against the current SDK but has **not** been executed in this repository, because no key was available.

## The files

| File | Pattern | Objective | Law | What it prints |
|---|---|---|---|---|
| `common.py` | the shared desk | | | nothing; `ask`, `ask_json`, `ask_async`, `trace`, the canned world, the stand-in client |
| `e1_augmented_llm.py` | augmented LLM | 1.3a | | two turns: `tool_use` then `end_turn`, and the JSON triage |
| `e2_chaining.py` | prompt chaining | 1.3b | 2 | classify, gate, draft, then the gate rejecting a mumbled category |
| `e3_routing.py` | routing | 1.3b | 1, 2 | the ward the nurse picked and its model, the specialist's reply, the default ward |
| `e4_parallel.py` | parallelization | 1.3b | | three scouts' wall clock versus sequential; three judges' majority |
| `e5_orchestrator_workers.py` | orchestrator-workers | 1.5 | 4 | the model-written plan, each worker's finding with its declared needs, one recommendation |
| `e6_evaluator_optimizer.py` | evaluator-optimizer | 1.3b | 3 | draft word count, editor's criticism, revision, PASS |
| `e7_agent_loop.py` | the agent loop | 1.3c | 3 | one `stop_reason` per turn, the final text or an escalation with a reason |
| `e8_replanning.py` | re-planning | 1.5 | 3, 4 | run lines, the replan that drops task 3 and adds two, the growth budget, the recommendation |

## E7 scenarios

`D1_SCENARIO` steers the stand-in's final reply so each branch of E7's `match` can be watched:

| Value | What the stand-in does | Branch exercised |
|---|---|---|
| `default` | tool_use, tool_use, end_turn | the healthy trace |
| `truncate` | the final reply arrives as `max_tokens`, then completes after `Continue.` | truncated is not done |
| `refuse` | the final reply is a `refusal` with `stop_details` | a different path, no blind retry |
| `exhaust` | asks for the phone on every turn | the floor: budget exhausted, human hand-off with a reason |

## Where this departs from the book, and why

- **DRY_RUN is a stand-in, not an early return.** The book's exhibits return a canned verdict and stop before any call. Here the dry run swaps the client instead, so you can watch `stop_reason` steer the loop with zero paid calls. Both make no paid calls. This is the same trick the Domain 3 lab used in `e5_hybrid.py`, where DRY_RUN swapped the paid embedder for the toy foreman.
- **Model IDs** were checked against the current API reference. The book's September-2026 alias `claude-sonnet-5` is replaced by the current tiers in `common.py`: `claude-opus-5-5` for judgement and money, `claude-sonnet-5-5` for explanation, `claude-haiku-4-5` for one-word sorts. Change them in one place.
- **No server-side fallbacks.** Production code on these models would normally add the `fallbacks` parameter so a refusal is retried on another model. It is left out on purpose so E7's `refusal` branch is exercised as the book intends: the loop escalates to a human with a reason.
- **`text_of()` instead of `content[0].text`.** Current models may place thinking blocks before the text, so the exhibits read the text blocks by type. Assistant turns are replayed whole, blocks unchanged.
- **E8's new subtasks are proper task records** with fresh ids and empty `needs`, and additions are clipped at the cap. The book's sketch appended bare strings.
- **`max_tokens` is 1024** rather than the book's 500 to 1000, because thinking tokens count toward it on current models.
- **E4 sleeps 0.2 s per scout on battery** so the slowest-scout lesson shows as a number, not a sentence.

## Reading order for the exam

E1 is the cell. E2, E3, E4, E6 are arrangements of the cell where code owns the path (Law 2). E7 is the one arrangement where the model owns the path, bounded by a budget and an exit (Law 3). E5 and E8 are the two levels of decomposition above chaining (Law 4). Run `./run_all.sh` once, then cover the output and predict what each file prints before running it again. The companion explainer is `../D1_Explained_COMBINED_All_8_Parts.pdf`.
