# d7/ — Developer Productivity lab: the debug ladder, permission modes, miss families

A runnable companion to `CCAR-P_D7_Summary.pdf` (objective 7.3 and the permission-mode line above it). It simulates one Claude Code workstation in plain Python (`world.py`): five settings layers, hooks, MCP servers, permission rules, memory files and an install. Everything the exhibits print is computed from that data.

Claude Fable 5.1 (`claude-fable-5-1`, the newest Fable; there is no 5.5) plays the student. It predicts the cheapest debug rung, the permission grid and the quiz answers. The code then grades it. Model calls give soft judgement and code supplies the hard grading.

## Run

```bash
cd d7
python e1_debug_ladder.py          # 7 calls, effort low
python e2_permission_modes.py      # 1 call
python e3_miss_families.py         # 5 calls
python e3_miss_families.py --me    # you take the quiz; no API call, graded the same way

# on battery (no key, no cost): Windows PowerShell  $env:DRY_RUN = "1"   ·   Linux/Mac  DRY_RUN=1 python ...
```

The key comes from the repo-root `.env`, as in d1, d2 and d3. Every call opts into the server-side fallback and prints `[answered by ...]` if another model answered.

## The files

| File | What it is |
|---|---|
| `world.py` | the simulated workstation. Settings layers from user up to managed, the merge, `decide_rules` (deny, then ask, then allow), and one function per ladder rung. Edit it to break the setup a different way. |
| `e1_debug_ladder.py` | seven tickets. Fable names the first command to run. The code climbs `/status`, `/hooks`, `/mcp`, `/permissions`, `/context`, `/doctor` and `--debug` in order, and stops at the first rung whose output shows the cause. That rung is the right answer. |
| `e2_permission_modes.py` | eight actions under `default`, `acceptEdits`, `plan`, `auto`, `dontAsk` and `bypassPermissions`. The code computes the grid, Fable predicts it, and every miss is explained. |
| `e3_miss_families.py` | five exam stems. Each wrong option carries its family: CM, OP, SD, TR, VG, OE or HL. Fable answers and labels the families, or you do with `--me`. |
| `common.py`, `standin.py`, `ask_about.py` | the shared desk, the battery stand-in and the question helper, the same as the other folders |

## What the battery run prints

```
e1  ladder bars by output size / 7 tickets: Fable's pick, the rungs climbed, the answering rung's output with » on the cause / 6 of 7 (the stand-in slips on ticket 6)
e2  starts in acceptEdits / 8 x 6 grid with ✓ and ✗ / the one miss explained / per-mode counts / 47 of 48
e3  5 questions, answer and family per wrong option / 5 of 5 answers, 14 of 15 families, a bar per family
```

## Caveats

- The `auto` column uses a **simulated** classifier: low-risk actions pass and high-risk ones are blocked when no rule applies. The real classifier is a model, so check the docs for edge cases.
- On this workstation, managed settings disable `bypassPermissions`, so that column reads N/A. That is itself a 7.x fact: IT can switch the mode off for everyone.
- `world.py` is a teaching model of Claude Code, not Claude Code itself. The command names and what each answers come from the D7 summary's table.
