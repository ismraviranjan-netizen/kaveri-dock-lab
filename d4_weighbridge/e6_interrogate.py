# e6_interrogate.py — four suspects, cheapest convicting test first; one change per replay
import json, re

RC = {"prompt": "v1.9", "model": "claude-sonnet-5-5", "index": "sop-2026-09-27"}  # manifest
FLIPPED = ["G-031", "G-058", "G-077", "G-102", "G-140", "G-163", "G-188"]

def retrieval(traces):                            # free: read what was actually fetched
    chunks = [c for t in traces for c in t["chunks"]]
    stale = [c["id"] for c in chunks if c["index"] != RC["index"]]
    return f"{len(chunks) - len(stale)}/{len(chunks)} chunks from {RC['index']}", not stale

def model(receipts):                              # free: who actually answered?
    seen = sorted({r["model"] for r in receipts})
    return f"served by {seen}", seen == [RC["model"]]

def hallucination(replies, sop_clauses):          # cheap: every cited clause must exist
    cited = {c for r in replies for c in re.findall(r"SOP \d+ §\d+", r)}
    ghosts = cited - sop_clauses
    return f"{len(cited) - len(ghosts)}/{len(cited)} cited clauses exist", not ghosts

def prompt(replay):                               # one change: the prompt, nothing else
    old = sum(replay(cid, prompt="v1.8") for cid in FLIPPED)
    new = sum(replay(cid, prompt="v1.9") for cid in FLIPPED)
    return f"v1.8 {old}/7 pass · v1.9 {new}/7 pass", old == new

if __name__ == "__main__":                        # DRY_RUN: recorded traces, receipts, replays
    fx = json.load(open("friday_fixtures.json", encoding="utf-8"))
    replay = lambda cid, prompt: fx["replays"][prompt][cid]
    for name, (detail, cleared) in [
            ("retrieval", retrieval(fx["traces"])), ("model", model(fx["receipts"])),
            ("hallucination", hallucination(fx["replies"], set(fx["sop_clauses"]))),
            ("prompt", prompt(replay))]:
        print(f"{name:<14}{'CLEARED' if cleared else 'GUILTY':<9}{detail}")
