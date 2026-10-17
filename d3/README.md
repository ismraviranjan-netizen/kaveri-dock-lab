# d3/ — the Loading Dock exhibits, runnable

The nine code exhibits from `CCAR-P_D3_Loading_Dock.pdf` and `CCAR-P_D3_Dock_Lab_Kit.pdf` (E1 to E8, plus the E9 one-ticket walk), rewritten in the same shape as `../d1/`: plain, step-numbered Python files that run, print, and can be read top to bottom. One set of files, used both for the dry run and for live API calls. The original hand-typeable versions stay in the repo root (`../e1_kaveri_mcp.py` and friends); these are the practice versions with the Messages API wired in.

## Run

```bash
pip install anthropic fastmcp          # once. fastmcp is only for E1 and E9 (the MCP server)

# live: ANTHROPIC_API_KEY in a .env file in the repo root (git-ignored; see ../.env.example)
cd d3
python e1_connector.py

# on battery: zero paid calls, no key needed
DRY_RUN=1 python e1_connector.py              # Linux / Mac
set DRY_RUN=1                                 # Windows Command Prompt, then: python e1_connector.py
$env:DRY_RUN = "1"                            # Windows PowerShell

$env:PRETTY = "1"                             # optional, any OS: indent the JSON log lines of E7 and E9 for reading
./run_all.sh     or     run_all.bat           # all nine, on battery
```

`DRY_RUN=1` makes `make_client()` return the scripted stand-in in `standin.py`. The exhibits run their real control flow (the same `stop_reason` branches, the same `tool_result` round-trips), but every reply is canned and nothing leaves the machine. E7's canned day (`data/logday.jsonl`, 40,000 lines) is written the first time E7 runs, or by `python gen_logday.py`.

## Models

| Constant | Model | Used for |
|---|---|---|
| `MODEL` | `claude-fable-5-1` | everything: drafting, the E1 and E3 tool loops, E5's live foreman, `count_tokens` (free endpoint, the model only picks the tokenizer) |

One model, one constant, in `common.py`. Every `ask*()` call goes through `create_message()`, which opts into the API's server-side fallback: if Fable's safety classifier declines an ordinary request, the API re-runs it on the model Anthropic recommends, inside the same call, instead of the exhibit crashing. Fable 5.1 is the latest and most capable model: $10 per million input tokens and $50 per million output tokens, thinking always on (it counts toward `max_tokens`), and it needs an account on 30-day data retention. A whole live run of the nine files is about a dozen calls plus free `count_tokens` calls: a few dollars at most.

## The files

| File | What it is | Objective | Law |
|---|---|---|---|
| `ask_about.py` | not an exhibit: a helper. Run any exhibit into a file, then `python ask_about.py e7_out.txt` and ask questions about that output in a conversation | | |
| `common.py` | the shared desk: the switch, `.env` loader, models, a rough price list, SOP 214 and the nine-tool belt from `data/`, the tool functions, `text_of`, `trace`, `tool_result`, `make_client`, `ask`, `ask_json`, `ask_usage`, `count_tokens` | | |
| `standin.py` | the dry-run stand-in. Not needed to learn the patterns | | |
| `e1_connector.py` | a FastMCP server with two tools, a resource, a prompt; the in-process probe; then the model works a ticket with the resource in context, the prompt as the user turn, and tools dispatched through the MCP client | 3.7 | 1 |
| `e2_bloat_audit.py` | price the nine-tool belt against the three the logs use, times the day's traffic; the lookalike pair | 3.1 | 1 |
| `e3_gate_pass.py` | scopes in a table, `authorize -> audit -> tool`; three callers at the refund door; then the model asks for `process_refund`, the gate denies it as a `tool_result` error, the model escalates | 3.2 | 1 |
| `e4_chunking.py` | SOP 214 cut by tape measure, by heading, with overlap; is the procedure whole; then the model answers from one fixed box and from one heading chunk | 3.5 | 2 |
| `e5_hybrid.py` | the register (BM25-ish) and the foreman (toy on battery, the model scoring sections live), fused with `W_SEM`; each query shown register-only, foreman-only, hybrid | 3.6, 3.5 | 3 |
| `e6_shape_router.py` | regex routes: aggregate language first, then an id, then the shelves; only the RAG road calls the model | 3.6 | 3 |
| `e7_dock_cameras.py` | one ticket writes four JSON lines with one trace id; the draft stage is a real call and its `usage` becomes tokens and paise; then the canned day digested to mean and p95 | 3.4 | 4 |
| `e8_two_bills.py` | nine full schemas versus nine one-line stubs, measured; then the three bills: monolithic, progressive, small+cached | 3.8 | 5 |
| `e9_one_ticket.py` | the eight hops on one request, with the gate, the connector, the shelves, the priced window, the carrier timeout and a real draft call, all on one trace id | all | all |
| `e10_two_lanes.py` | the Part 4 drawing as code: INGEST lane (chunk on headings, ★ situate with one model call, build the vector and BM25 indexes) and QUERY lane (search both, fuse, rerank with one model call, generate from a cached preamble + top-N); the shelves are built plain and situated so you can watch where section 4 ranks for a customer's question | 3.5, 3.6 | 2, 3 |
| `gen_logday.py` | writes `data/logday.jsonl` for E7 | | |
| `data/` | `sop_214.md`, `tools_all9.json` (copies of the root files), `logday.jsonl` (generated, git-ignored) | | |

## What each file prints on battery

```
e1  tools/list -> 2 tools, resources/list -> sop://214, prompts/list -> customs_triage / turn 1 tool_use (get_shipment_status) / turn 2 tool_use (find_alternate_carriers) / turn 3 end_turn / the re-filing summary
e2  9 tools: 725 tokens / 3 tools: 274 tokens / belt tax: 18,040,000 tokens/day / the lookalike pair
e3  kavi-agent DENY, refund-desk ALLOW, carrier-portal-v1 ALLOW (the wildcard) / the fix: DENY / model: get_shipment_status ALLOW, process_refund DENY, escalate_to_human ALLOW, end_turn
e4  fixed 8 chunks False / heading 10 chunks True / box 4 holds Step 1 and 2 only / fixed box answer: MISSING Step 3-6 / heading chunk answer: all six present
e5  q1 register-only puts section 4 first, foreman-only puts section 3 first (Padma's incident), hybrid puts section 4 first / q2 all three put section 1 first
e6  structured_lookup -> the TMS row / sql_aggregate -> 41 / "How many times has KF-2481" -> sql_aggregate (rule order) / hybrid_rag -> drafted from section 4
e7  four JSON lines, one trace id, draft tokens=473 cost_pc=(from the price list in common.py) / retrieve mean= 395ms p95= 2,349ms <- the mean lied
e8  schemas 725 vs stubs 423 / monolithic 361,445 / progressive 4,403 + 1 round-trip / small+cached 4,302 / gap 82x
e9  nine register lines on one trace id: route, authz, tool, resource, retrieve, assemble, carrier_eta, draft, total / the answer cites section 4, promised_date=false
```

## Live versus battery: what to expect

- The `stop_reason` trace in E1 and E3 should match the battery run line for line. The wording will not. A live E1 may skip `find_alternate_carriers`: the prompt card never asked for carriers.
- E2 and E8 live use the API's own `count_tokens`, which is free and larger than the four-characters bench. The Dock saw 2,314 / 811 for the belts. Whatever the exact count, the shape is the point.
- E4 live: the model should list Steps 1 and 2 from the fixed box and say MISSING for 3 to 6. If it fills in the rest from memory, that is exactly the failure to notice: the excerpt did not contain them.
- E5 live: the foreman is one call that scores the ten section titles 0 to 10, then the fusion is the same code. Expect section 4 at rank 1 for both queries once both halves run.
- E10 live: five calls in all (situate, then rerank and generate for each of two questions). The 'where section 4 ranks' lines are the lesson: for the customer's wording ('parcel stuck, paperwork problem') the plain shelves rank section 4 low on both indexes, and the situated shelves should lift it, because the model-written sentence in front of the chunk uses the customer's words. The `cache_read` figure on the second question's generate line should be non-zero: the preamble came back from the cache. No battery line is recorded for E10 yet.
- E7 and E9 live: the draft line carries the real `usage` numbers and a paise figure from the price list in `common.py`. The price list is approximate; edit it.
- The toy foreman and the canned log day exist only on battery.

## Where this departs from the Dock Lab Kit, and why

- **DRY_RUN is a stand-in, not an early return.** The kit's scripts estimated or skipped the paid path. Here the dry run swaps the client, so the real control flow runs with zero paid calls. Same trick as `../d1/`.
- **Every exhibit touches the API where the lesson needs it.** E1 dispatches the model's tool calls through MCP; E3 hands the gate's denial back as a `tool_result` error; E4 lets the model read from one chunk; E5 uses the model as the semantic half; E6 drafts on the RAG road; E7 and E9 log a real `usage` block. The kit's E2 and E8 arithmetic is unchanged.
- **E6's rule order** puts aggregate language before the id pattern, so "How many times has KF-2481 been delayed?" counts instead of returning one row (the kit's sabotage lesson, Dock Book II Q35).
- **E3 gives kavi-agent an escalation scope**, so the denied refund has a legal next move. The audit line is written for denials too.
- **The model ID** is current: `claude-fable-5-1`, in one place in `common.py`.
- **`max_tokens` is 128,000**, the model's hard ceiling (the API rejects more). Thinking counts toward it, so a cut-off reply is next to impossible; if one happens anyway the code raises a clear error instead of returning empty text. `make_client` sets a 600-second timeout, which the SDK requires before it will send a non-streaming call with a cap this high.

## Reading order for the exam

E1 is the connector: three primitives, one bridge to the Messages API tool list. E2 and E3 are the two costs of every door (tokens, and who holds the key). E4 and E5 are the shelves: cut along meaning, search with both halves. E6 is the rule that picks the machine from the shape of the data. E7 is the plumbing every other number came from. E8 is the bill. E9 is all of it on one ticket. Run everything on battery once, then cover the output and predict what each file prints before running it again. Then run the sabotage labs from `../CCAR-P_D3_Dock_Lab_Kit.pdf` on these files and ledger every surprise in `../ledger.md`.
