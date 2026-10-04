# E4 · Parallelization: three scouts, or three judges  (objective 1.3b, workflow 3)
#
#   Sectioning: three DIFFERENT questions at once (three scouts on three roads). Purpose: coverage, speed.
#   Voting:     the SAME question three times (three judges). Purpose: confidence. Costs 3x.
# Same trick, simultaneity, opposite purposes. The CODE drew the fork; no model chose to parallelize.
#
# Run on battery:  DRY_RUN=1 python e4_parallel.py   (each call sleeps 0.2 s)      Run live:  python e4_parallel.py

import asyncio
import time
from common import ask_async, MODEL_SMALL, MODEL_MAIN, CLAIM_TEXT, DRY_RUN


# ---------------------------------------------------------------
# STEP 0. Things we decide before talking to the model
#         (ask_async in common.py uses the async SDK client, so several calls can be in flight at once)
# ---------------------------------------------------------------

CONSIGNMENT = "KF-2481"
CARRIERS = ["BlueDart", "Delhivery", "IndiaPost"]


# ---------------------------------------------------------------
# STEP 1. SECTIONING: three different questions, all at once
# ---------------------------------------------------------------

async def check_one_carrier(carrier):
    question = (
        "In one line, give a plausible ETA for consignment " + CONSIGNMENT
        + " on the Pune-Chennai lane if re-routed via " + carrier + ". "
        "Assume it is currently held at customs. Start your line with the carrier name."
    )
    return await ask_async(MODEL_SMALL, question)


async def sectioning():
    # asyncio.gather starts all three and waits for the slowest. Wall clock = the slowest scout.
    return await asyncio.gather(
        check_one_carrier(CARRIERS[0]),
        check_one_carrier(CARRIERS[1]),
        check_one_carrier(CARRIERS[2]),
    )


async def sequential():
    # The same three questions one after another, for comparison. Wall clock = the sum.
    results = []
    for carrier in CARRIERS:
        results.append(await check_one_carrier(carrier))
    return results


# ---------------------------------------------------------------
# STEP 2. VOTING: the same question three times, majority wins
# ---------------------------------------------------------------

async def one_vote():
    question = (
        "You are a claims reviewer at Kaveri Freight. Read this refund claim and reply with "
        "exactly one word, APPROVE or REJECT. No explanation.\n\n" + CLAIM_TEXT
    )
    return await ask_async(MODEL_MAIN, question)


def count_votes(votes):
    # Plain Python counts. No fourth model call to decide the majority.
    approve_count = 0
    reject_count = 0
    for vote in votes:
        if "APPROVE" in vote.upper():
            approve_count = approve_count + 1
        else:
            reject_count = reject_count + 1
    if approve_count > reject_count:
        return "APPROVE"
    return "REJECT"


async def voting():
    votes = await asyncio.gather(one_vote(), one_vote(), one_vote())
    return votes, count_votes(votes)


# ---------------------------------------------------------------
# STEP 3. Run both, and time the sectioning against the sequential version
# ---------------------------------------------------------------

async def main():
    print("=== Sectioning: three scouts at once ===")
    start = time.perf_counter()
    scouts = await sectioning()
    parallel_seconds = time.perf_counter() - start
    for line in scouts:
        print("  scout ->", line)

    print()
    print("=== The same three scouts, one after another ===")
    start = time.perf_counter()
    await sequential()
    sequential_seconds = time.perf_counter() - start
    print("Parallel took", round(parallel_seconds, 2), "s (about the slowest single call).")
    print("Sequential took", round(sequential_seconds, 2), "s (about the sum of all three).")

    print()
    print("=== Voting: three judges on one refund claim ===")
    votes, majority = await voting()
    print("Votes:", list(votes))
    print("Majority:", majority)
    print("Note: three calls for one decision. Spend that on refunds, not on apologies.")


if __name__ == "__main__":
    print("# E4 · parallelization · " + ("DRY_RUN (each call sleeps 0.2 s)" if DRY_RUN else "LIVE"))
    asyncio.run(main())
