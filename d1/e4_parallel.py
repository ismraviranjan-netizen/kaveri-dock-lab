# E4 · Parallelization — three scouts (sectioning: coverage) or three judges (voting: confidence) (objective 1.3b, workflow 3)
# Same trick, simultaneity, opposite purposes. Your code drew the fork; no model chose to parallelize.
import asyncio, time
from common import ask_async, MODEL_SMALL, MODEL_MAIN, CLAIM_TEXT, DRY_RUN

async def check(carrier, cid):                          # one scout, one road
    return await ask_async(MODEL_SMALL, f"ETA for {cid} via {carrier}? One line.")

async def sectioning(cid):                              # coverage: different subtasks, all at once
    return await asyncio.gather(check("BlueDart", cid), check("Delhivery", cid), check("IndiaPost", cid))

async def sequential(cid):                              # the same three scouts, one after another, for comparison
    return [await check(c, cid) for c in ("BlueDart", "Delhivery", "IndiaPost")]

async def voting(claim):                                # confidence: same subtask x3, majority wins
    verdicts = await asyncio.gather(*[
        ask_async(MODEL_MAIN, "APPROVE or REJECT only. Refund claim:\n" + claim) for _ in range(3)])
    return verdicts, max(set(verdicts), key=verdicts.count)

if __name__ == "__main__":
    print(f"# E4 · parallelization · {'DRY_RUN (each scout sleeps 0.2 s)' if DRY_RUN else 'LIVE'}")
    t = time.perf_counter(); scouts = asyncio.run(sectioning("KF-2481")); par = time.perf_counter() - t
    t = time.perf_counter(); asyncio.run(sequential("KF-2481"));         seq = time.perf_counter() - t
    for s in scouts: print("  scout ->", s)
    print(f"# sectioning wall clock {par:.2f} s (slowest scout) vs sequential {seq:.2f} s (the sum)")
    verdicts, majority = asyncio.run(voting(CLAIM_TEXT))
    print(f"# voting: {verdicts} -> majority {majority}  (3x cost for one decision: spend it on refunds, not apologies)")
