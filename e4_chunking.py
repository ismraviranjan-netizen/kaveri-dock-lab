# E4 · Chunking three ways on SOP 214 (objective 3.5)
import re
doc = open("sops/sop_214.md", encoding="utf-8").read()

def fixed(text, size=180):                     # the tape measure: N words per box
    w = text.split()
    return [" ".join(w[i:i+size]) for i in range(0, len(w), size)]

def by_heading(text):                          # the seams: cut before every # or ## line
    parts = re.split(r"(?m)^(?=#{1,2} )", text)
    chunks = []
    for p in parts:
        p = p.strip()
        if not p: continue
        first = p.splitlines()[0]
        title = "Preamble" if first.startswith("# ") else first.lstrip("# ").strip()
        chunks.append(f"[SOP 214 - {title}]\n{p}")   # label inside the box
    return chunks

def with_overlap(chunks, tail=30):             # carry the last `tail` words forward
    out = [chunks[0]]
    for prev, cur in zip(chunks, chunks[1:]):
        out.append(" ".join(prev.split()[-tail:]) + " " + cur)
    return out

def whole(chunks):
    return any("Step 1" in c and "Step 6" in c for c in chunks)

if __name__ == "__main__":
  F, H = fixed(doc), by_heading(doc)
  print(f"fixed   : {len(F)} chunks | full procedure in one chunk: {whole(F)}")
  print(f"heading : {len(H)} chunks | full procedure in one chunk: {whole(H)}")
  for i, c in enumerate(F, 1):
    starts = re.findall(r"## (\d)\.", c)
    if any(s in ("3", "4", "5") for s in starts):
        print(f"fixed box {i}: sections starting inside {starts} | 'e-way bill' x{c.count('e-way bill')} "
              f"| 'cancel' x{c.lower().count('cancel')} | Step 1 {'Step 1' in c} Step 6 {'Step 6' in c}")
