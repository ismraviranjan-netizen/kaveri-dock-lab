# json_four_ways.py — load, loads, dump, dumps: the four doors between JSON text and Python objects
# Run it from this folder:  python json_four_ways.py
# Rule to remember: load/dump talk to FILES, loads/dumps talk to STRINGS. The "s" means string.
import json

print("=" * 70)
print("PART 1 · json.loads  —  a STRING of JSON text  ->  a Python object")
print("=" * 70)
text = '{"id": "KF-2481", "status": "CUSTOMS_HOLD", "days": 3, "safe": true, "note": null}'
print("before:", type(text).__name__, "->", text)          # it is only text right now
obj = json.loads(text)                                       # parse the string
print("after :", type(obj).__name__, "->", obj)             # now it is a real dict
print("proof it is real data: obj['days'] + 1 =", obj["days"] + 1)
print("JSON true -> Python", obj["safe"], "| JSON null -> Python", obj["note"])

print()
print("=" * 70)
print("PART 2 · json.dumps  —  a Python object  ->  a STRING of JSON text")
print("=" * 70)
record = {"id": "G-001", "slice": "real", "triage_ok": True, "latency_s": 0.75, "owner": None}
print("before:", type(record).__name__, "->", record)
as_text = json.dumps(record)                                 # the reverse of loads
print("after :", type(as_text).__name__, "->", as_text)
print("Python True -> JSON true | Python None -> JSON null | quotes become double quotes")
print("pretty version (indent=2):")
print(json.dumps(record, indent=2))

print()
print("=" * 70)
print("PART 3 · json.dump  —  a Python object  ->  written into a FILE")
print("=" * 70)
runs = [                                                     # a tiny version of runs_v1_8.json
    {"id": "G-001", "triage_ok": True,  "latency_s": 0.75},
    {"id": "G-002", "triage_ok": False, "latency_s": 1.80},
    {"id": "G-003", "triage_ok": True,  "latency_s": 0.93},
]
with open("demo_one_document.json", "w", encoding="utf-8") as f:
    json.dump(runs, f, indent=1)                             # ONE document: a list with 3 dicts
print("wrote demo_one_document.json; the file contains:")
print(open("demo_one_document.json", encoding="utf-8").read())

print("=" * 70)
print("PART 4 · json.load  —  a FILE  ->  a Python object   (this is E1 line 30)")
print("=" * 70)
with open("demo_one_document.json", encoding="utf-8") as f:
    data = json.load(f)                                      # read the whole file at once
print("type:", type(data).__name__, "| items:", len(data))
print("data[0]['id'] =", data[0]["id"], "| data[1]['latency_s'] =", data[1]["latency_s"])
print("count of triage_ok True:", sum(r["triage_ok"] for r in data), "of", len(data))

print()
print("=" * 70)
print("PART 5 · JSONL: many documents, one per line   (this is E2 line 9)")
print("=" * 70)
with open("demo_many_lines.jsonl", "w", encoding="utf-8") as f:
    for r in runs:
        f.write(json.dumps(r) + "\n")                        # dumps once per record, newline after each
print("wrote demo_many_lines.jsonl; the file contains:")
print(open("demo_many_lines.jsonl", encoding="utf-8").read())
print("json.load on a JSONL file FAILS, because it is not one document:")
try:
    json.load(open("demo_many_lines.jsonl", encoding="utf-8"))
except json.JSONDecodeError as e:
    print("   JSONDecodeError:", e.msg, "at line", e.lineno)
rows = [json.loads(line) for line in open("demo_many_lines.jsonl", encoding="utf-8")]
print("the fix — loads once per line:", rows)

print()
print("=" * 70)
print("PART 6 · the two mistakes everyone makes once")
print("=" * 70)
try:
    json.loads(open("demo_one_document.json", encoding="utf-8"))   # loads wants a string, got a file
except TypeError as e:
    print("json.loads(file) -> TypeError:", e)
try:
    json.load(text)                                                 # load wants a file, got a string
except AttributeError as e:
    print("json.load(string) -> AttributeError:", e)

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("  json.load(file)      JSON file   -> Python      (E1 line 30: runs_v1_8.json)")
print("  json.loads(string)   JSON string -> Python      (E2 line 9, once per JSONL line; E3 line 5)")
print("  json.dump(obj, file) Python      -> JSON file   (gen_fixtures.py writes the data files)")
print("  json.dumps(obj)      Python      -> JSON string (one line of a JSONL file)")

# The two demo files stay on disk so you can open them in VS Code.
# To tidy up afterwards, uncomment the next three lines:
# import os
# os.remove("demo_one_document.json")
# os.remove("demo_many_lines.jsonl")
