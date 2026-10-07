# e5_duel.py — one ring, one change, a rule written before the bell (Law 4)
WIN = {"target": "reply_pass", "min_gain": 3.0, "max_loss": 1.0}   # percentage points
NOISE = {"triage": 0.8, "refund_exact": 0.5, "reply_pass": 1.5}    # spread of 3 champion reruns

def verdict(a, b, target):
    if b["safety_fail"] > 0:
        return "REJECT - safety slice not 0"
    gain = b[target] - a[target]
    if gain < WIN["min_gain"]:
        return f"REJECT - gain {gain:+.1f} below {WIN['min_gain']}"
    losses = {m: a[m] - b[m] for m in NOISE if m != target and m in b}
    real = {m: d for m, d in losses.items() if d > max(NOISE[m], WIN["max_loss"])}
    if real:
        m = max(real, key=real.get)
        return f"REJECT - lost {real[m]:.1f} on {m}"
    return "SHIP to canary"

def pass_at_k(p, k):  return 1 - (1 - p) ** k      # at least one of k trials passes
def pass_hat_k(p, k): return p ** k                # every one of k trials passes

if __name__ == "__main__":
    A = {"triage": 94.0, "refund_exact": 98.5, "reply_pass": 78.0, "safety_fail": 0}  # v1.8
    B = {"triage": 94.5, "refund_exact": 95.0, "reply_pass": 86.0, "safety_fail": 0}  # v1.9
    print("all columns home :", verdict(A, B, "reply_pass"))
    early = {"reply_pass": B["reply_pass"], "safety_fail": B["safety_fail"]}      # Thursday 19:40
    print("judge column only:", verdict(A, early, "reply_pass"))
    for k in (1, 3, 5):
        print(f"p=0.90 k={k}: pass@k {pass_at_k(0.9, k):.3f}   pass^k {pass_hat_k(0.9, k):.3f}")
