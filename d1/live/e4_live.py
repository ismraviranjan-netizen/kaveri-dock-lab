# e4_live.py
# E4: parallelization. Same trick (several calls at the same time), two opposite purposes.
#   Sectioning: three DIFFERENT questions at once (three scouts on three roads). Purpose: coverage, speed.
#   Voting:     the SAME question three times (three judges). Purpose: confidence. Costs 3x.
# The code drew the fork. No model decided to parallelize.
#
# Before running:   pip install anthropic   and   ANTHROPIC_API_KEY in the environment
# Run:              python e4_live.py

import asyncio
import time
import anthropic


# ---------------------------------------------------------------
# STEP 0. Things we decide before talking to the model
# ---------------------------------------------------------------

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 256                  # short answers are all we need here

CONSIGNMENT = "KF-2481"
CARRIERS = ["BlueDart", "Delhivery", "IndiaPost"]

# The refund claim the three judges will vote on.
CLAIM = """Refund claim: consignment KF-1177, declared value Rs 18,500.
Two cartons water-damaged on arrival at the Bengaluru hub. Customer requests a full refund.
Photos attached show a tear in the outer packaging; inner goods wet. Carrier: Delhivery.
Insurance: declared-value cover active. Delivery was signed for without a damage note.
"""


# ---------------------------------------------------------------
# STEP 1. Connect with the ASYNC client. "async" lets several calls be in flight at once.
# ---------------------------------------------------------------

client = anthropic.AsyncAnthropic()

async def ask(question):
    reply = await client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": question}],
    )
    if reply.stop_reason == "refusal":
        raise RuntimeError("The model declined to answer.")
    answer = ""
    for block in reply.content:
        if block.type == "text":
            answer = answer + block.text
    return answer.strip()


# ---------------------------------------------------------------
# STEP 2. SECTIONING: three different questions, all at once.
# ---------------------------------------------------------------

async def check_one_carrier(carrier):
    question = (
        "In one line, give a plausible ETA for consignment " + CONSIGNMENT
        + " on the Pune-Chennai lane if re-routed via " + carrier + ". "
        "Assume it is currently held at customs. Start your line with the carrier name."
    )
    return await ask(question)

async def sectioning():
    # asyncio.gather starts all three and waits for the slowest. Wall clock = slowest scout.
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
# STEP 3. VOTING: the same question three times, majority wins.
# ---------------------------------------------------------------

async def one_vote():
    question = (
        "You are a claims reviewer at Kaveri Freight. Read this refund claim and reply with "
        "exactly one word, APPROVE or REJECT. No explanation.\n\n" + CLAIM
    )
    return await ask(question)

async def voting():
    votes = await asyncio.gather(one_vote(), one_vote(), one_vote())

    # Count the votes in plain Python.
    approve_count = 0
    reject_count = 0
    for vote in votes:
        if "APPROVE" in vote.upper():
            approve_count = approve_count + 1
        else:
            reject_count = reject_count + 1

    if approve_count > reject_count:
        majority = "APPROVE"
    else:
        majority = "REJECT"
    return votes, majority


# ---------------------------------------------------------------
# STEP 4. Run both, and time the sectioning against the sequential version.
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
    print("Votes:", votes)
    print("Majority:", majority)
    print("Note: this cost three calls for one decision. Spend that on refunds, not on apologies.")

asyncio.run(main())
