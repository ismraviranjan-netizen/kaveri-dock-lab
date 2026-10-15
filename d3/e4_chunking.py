# E4 · Chunking three ways on SOP 214, then ask the model from one box  (objective 3.5, Law 2)
#
#   Fixed size:  the tape measure. N words per box, wherever the cut falls.
#   By heading:  the seams. Cut before every # or ## line, and write the label INSIDE the box.
#   Overlap:     carry the tail of each box into the next. A dial, not a fix.
#   Then the question that matters: does the whole re-filing procedure (Step 1 to Step 6) sit in ONE chunk?
#   Finally the model answers from one chunk of each kind, so the retriever's mistake becomes the reader's.
#
# Run on battery:  DRY_RUN=1 python e4_chunking.py          Run live:  python e4_chunking.py

import re
from common import ask, MODEL_MAIN, SOP, DRY_RUN


# ---------------------------------------------------------------
# STEP 0. The dials
# ---------------------------------------------------------------

BOX_WORDS = 180                           # the tape measure. SOP 214 is ~1,330 words: 8 boxes
OVERLAP_WORDS = 30                        # how much of each box the next one repeats


# ---------------------------------------------------------------
# STEP 1. Three cutters. Plain Python, no model.
# ---------------------------------------------------------------

def fixed(text, size=BOX_WORDS):
    words = text.split()
    boxes = []
    for start in range(0, len(words), size):
        boxes.append(" ".join(words[start:start + size]))
    return boxes


def by_heading(text):
    parts = re.split(r"(?m)^(?=#{1,2} )", text)          # cut just before each heading line
    chunks = []
    for part in parts:
        part = part.strip()
        if part == "":
            continue
        first_line = part.splitlines()[0]
        if first_line.startswith("# "):
            title = "Preamble"
        else:
            title = first_line.lstrip("# ").strip()
        chunks.append("[SOP 214 - " + title + "]\n" + part)    # the label rides inside the box
    return chunks


def with_overlap(chunks, tail=OVERLAP_WORDS):
    out = [chunks[0]]
    for previous, current in zip(chunks, chunks[1:]):
        out.append(" ".join(previous.split()[-tail:]) + " " + current)
    return out


# ---------------------------------------------------------------
# STEP 2. The test that matters: is the procedure whole inside one chunk?
# ---------------------------------------------------------------

def whole(chunks):
    for chunk in chunks:
        if "Step 1" in chunk and "Step 6" in chunk:
            return True
    return False


def chunk_with_step1(chunks):
    for chunk in chunks:
        if "Step 1" in chunk:
            return chunk
    return chunks[0]


# ---------------------------------------------------------------
# STEP 3. The reader: the model answers from ONE chunk, and only that chunk.
# ---------------------------------------------------------------

def answer_from(chunk):
    question = (
        "Using ONLY the excerpt below, list the numbered re-filing steps (Step 1 to Step 6) you can find, "
        "one line each. If any step is not in the excerpt, write MISSING for it. Do not use outside knowledge.\n\n"
        "EXCERPT:\n" + chunk
    )
    return ask(MODEL_MAIN, question)


if __name__ == "__main__":
    print("# E4 · chunking · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL_MAIN))

    # STEP 4. Cut the SOP three ways and count.
    F = fixed(SOP)
    H = by_heading(SOP)
    O = with_overlap(F)
    print("fixed    : " + str(len(F)) + " chunks | full procedure in one chunk: " + str(whole(F)))
    print("heading  : " + str(len(H)) + " chunks | full procedure in one chunk: " + str(whole(H)))
    print("overlap  : " + str(len(O)) + " chunks | full procedure in one chunk: " + str(whole(O))
          + " | box 2 now starts: " + repr(" ".join(O[1].split()[:6])) + " ...")

    # STEP 5. Look inside the fixed boxes around sections 3, 4, 5: the cancel/re-file seam.
    print()
    print("=== Inside the fixed boxes near the seam ===")
    for i, box in enumerate(F, 1):
        starts = re.findall(r"## (\d)\.", box)
        if any(s in ("3", "4", "5") for s in starts):
            print("fixed box " + str(i) + ": sections starting inside " + str(starts)
                  + " | 'e-way bill' x" + str(box.count("e-way bill"))
                  + " | 'cancel' x" + str(box.lower().count("cancel"))
                  + " | Step 1 " + str("Step 1" in box) + " Step 6 " + str("Step 6" in box))

    # STEP 6. The model reads one chunk of each kind. Two calls.
    print()
    print("=== The model answers from the fixed box that holds Step 1 ===")
    print(answer_from(chunk_with_step1(F)))
    print()
    print("=== The model answers from the heading chunk that holds Step 1 ===")
    print(answer_from(chunk_with_step1(H)))
