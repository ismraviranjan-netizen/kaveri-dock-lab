# E7 · The cache: one line at the top turns reads into writes  (objective 2.5)
#
#   The SOP pack (about 2,400 tokens, above Fable's 512-token minimum) is marked with a cache breakpoint.
#   A: no breakpoint at all.  B: a timestamp placed ABOVE the pack, before the breakpoint.  C: the same
#   timestamp placed in the user turn, after the breakpoint. Each variant is sent twice; the second call's
#   usage shows whether the cache was read. One line in the wrong place and every call writes instead of reads.
#
# Run on battery:  DRY_RUN=1 python e7_cache_line.py         Run live:  python e7_cache_line.py

import time
from common import create_message, IN_USD, FX, CACHE_WRITE, CACHE_READ, DESK_CALLS_PER_DAY, MODEL, DRY_RUN

SOP = "Kaveri SOP pack.\n" + "\n".join(
    "Rule " + str(i) + ": before release, check the e-way bill, the invoice and the HSN code." for i in range(1, 121))
NAMES = {"A": "no cache", "B": "time on top", "C": "time in user"}


def build(variant, now):
    """The request for one variant: where the breakpoint goes, and where the changing line goes."""
    stamp = "Current time: " + now + "\n"
    top = stamp if variant == "B" else ""
    sop = {"type": "text", "text": top + SOP}
    if variant != "A":
        sop["cache_control"] = {"type": "ephemeral"}            # 5-minute cache
    tail = stamp if variant == "C" else ""
    user = tail + "KF-2481 is held at customs. Next step?"
    return [sop], [{"role": "user", "content": user}]


def send(variant):
    """One call. Returns input tokens, cache creation tokens, cache read tokens."""
    system, messages = build(variant, time.strftime("%H:%M:%S"))
    reply = create_message(model=MODEL, max_tokens=1024, system=system, messages=messages, output_config={"effort": "low"})
    u = reply.usage
    return u.input_tokens, getattr(u, "cache_creation_input_tokens", 0) or 0, getattr(u, "cache_read_input_tokens", 0) or 0


if __name__ == "__main__":
    print("# E7 · the cache line · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL) + " · SOP pack about " + format(len(SOP) // 4, ",") + " tokens")
    print()
    print("=== call 2 of each variant (call 1 writes the cache where there is one) ===")
    print("  " + "variant".ljust(17) + "input".rjust(7) + "creation".rjust(10) + "read".rjust(8) + "billed-eq".rjust(11) + "  input $")
    bill = {}
    for variant, name in NAMES.items():
        send(variant)                                           # call 1: writes the cache (B and C)
        time.sleep(2)
        i, written, read = send(variant)                        # call 2: does it read?
        bill[variant] = b = i + CACHE_WRITE * written + CACHE_READ * read
        print("  " + (variant + " " + name).ljust(17) + format(i, ",").rjust(7) + format(written, ",").rjust(10)
              + format(read, ",").rjust(8) + format(b, ",.0f").rjust(11) + "  $" + format(b * IN_USD, ".5f"))
    gap = (bill["B"] - bill["C"]) * IN_USD * DESK_CALLS_PER_DAY * FX
    print()
    print("B instead of C on " + format(DESK_CALLS_PER_DAY, ",") + " Desk calls a day: +Rs " + format(gap, ",.0f"))
    print("static first, dynamic last: the time goes after the breakpoint")
