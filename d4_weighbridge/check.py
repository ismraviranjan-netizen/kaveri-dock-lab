# check.py — re-weigh every exhibit against the output captured in expected/ (the PDF's numbers).
#   python check.py            run all eight, print PASS or a diff per exhibit
#   python check.py e5         run one exhibit
#   python check.py --record   overwrite expected/*.txt with today's output (only after a git restore!)
# Use it as the sabotage lab's scale: change ONE line, predict, run check.py, read the diff, restore.
import difflib, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

EXHIBITS = ["e1_scorecard", "e2_golden_set", "e3_graders", "e4_calibrate",     # the eight book exhibits, nothing else
            "e5_duel", "e6_interrogate", "e7_levers", "e8_watchman"]            # (variants like e3_graders_haiku.py are skipped)

def exhibits():
    return [os.path.join(HERE, name + ".py") for name in EXHIBITS]

def run(path):
    r = subprocess.run([sys.executable, os.path.basename(path)], cwd=HERE, env=ENV,
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout + (("\n[stderr]\n" + r.stderr) if r.returncode else "")

def main(argv):
    record = "--record" in argv
    picks = [a.lower() for a in argv if not a.startswith("--")]
    failed = 0
    for path in exhibits():
        name = os.path.basename(path)
        tag = name[:2]                                   # e1 .. e8
        if picks and tag not in picks and name[:-3] not in picks:
            continue
        exp_path = os.path.join(HERE, "expected", f"{tag}.txt")
        got = run(path)
        if record:
            open(exp_path, "w", encoding="utf-8").write(got)
            print(f"{name:<20} recorded {len(got.splitlines())} lines")
            continue
        want = open(exp_path, encoding="utf-8").read() if os.path.exists(exp_path) else ""
        if got == want:
            print(f"{name:<20} PASS  (matches the PDF's printed output)")
        else:
            failed += 1
            print(f"{name:<20} DIFF  (- expected  + got)")
            for line in difflib.unified_diff(want.splitlines(), got.splitlines(),
                                             "expected", "got", lineterm="", n=0):
                if not line.startswith(("---", "+++", "@@")):
                    print("    " + line)
    if not record:
        print(f"\n{len(exhibits()) - failed}/{len(exhibits())} exhibits print what the PDF printed"
              + ("" if not failed else "  <- a sabotage is live, or a fixture drifted"))
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
