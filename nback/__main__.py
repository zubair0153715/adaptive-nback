"""adaptive-nback: dual n-back working-memory trainer with adaptive levels.

Each trial shows a position (3x3 grid) + a letter. Respond whether the CURRENT
stimulus matches the one N steps back, for position and/or letter.

Adaptive rule: accuracy >= 80% -> N+1, < 60% -> N-1 (min 1, max 9).
History (sessions, streaks) stored in ~/.nback_history.json.

Usage:
    python -m nback            # interactive session (20 trials)
    python -m nback --trials 30 --start-n 2
"""
import argparse
import json
import os
import random
import sys
import time

HISTORY_PATH = os.path.expanduser("~/.nback_history.json")
LETTERS = "ABCDEFGH"
GRID = [(r, c) for r in range(3) for c in range(3)]

def load_history():
    try:
        with open(HISTORY_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"sessions": []}

def save_history(h):
    with open(HISTORY_PATH, "w") as f:
        json.dump(h, f, indent=1)

def gen_sequence(n_trials, rng, match_prob=0.3):
    """Build sequence with guaranteed match opportunities."""
    seq = [(rng.choice(GRID), rng.choice(LETTERS))]
    return seq, match_prob

def run_session(n, n_trials=20, rng=None, responder=None, delay=1.6, silent=False):
    """responder(trial_idx, pos, letter) -> (pos_match: bool, letter_match: bool).
    If None, prompts the user interactively. Returns session dict."""
    rng = rng or random.Random()
    seq = [(rng.choice(GRID), rng.choice(LETTERS)) for _ in range(n_trials)]
    # force some matches so the task is meaningful
    for i in range(n, n_trials):
        if rng.random() < 0.35:
            p, l = seq[i - n]
            seq[i] = (p if rng.random() < 0.5 else rng.choice(GRID),
                      l if rng.random() < 0.5 else rng.choice(LETTERS))
    hits = fa = miss = cr = 0
    details = []
    for i, (pos, letter) in enumerate(seq):
        if not silent:
            r, c = pos
            grid = [["·"] * 3 for _ in range(3)]
            grid[r][c] = "●"
            print(f"\n--- trial {i+1}/{n_trials} (N={n}) ---")
            for row in grid:
                print(" ".join(row))
            print(f"letter: {letter}")
        if i < n:
            if not silent:
                print("(warm-up, no response needed)")
                time.sleep(delay)
            continue
        exp_pos = seq[i][0] == seq[i - n][0]
        exp_let = seq[i][1] == seq[i - n][1]
        if responder:
            got_pos, got_let = responder(i, pos, letter)
        else:
            ans = input("position match? [y/n] ").strip().lower()
            got_pos = ans.startswith("y")
            ans = input("letter match?   [y/n] ").strip().lower()
            got_let = ans.startswith("y")
        for exp, got in ((exp_pos, got_pos), (exp_let, got_let)):
            if exp and got:
                hits += 1
            elif exp and not got:
                miss += 1
            elif not exp and got:
                fa += 1
            else:
                cr += 1
        details.append({"trial": i, "exp": (exp_pos, exp_let), "got": (got_pos, got_let)})
        if not silent:
            time.sleep(0.3)
    total = hits + miss + fa + cr
    acc = (hits + cr) / total if total else 0
    if acc >= 0.80:
        new_n = min(9, n + 1)
    elif acc < 0.60:
        new_n = max(1, n - 1)
    else:
        new_n = n
    return {"n": n, "trials": n_trials, "hits": hits, "fa": fa,
            "miss": miss, "cr": cr, "accuracy": round(acc, 3),
            "next_n": new_n, "ts": time.time()}

def streak_days(sessions):
    days = sorted({time.strftime("%Y-%m-%d", time.localtime(s["ts"])) for s in sessions},
                  reverse=True)
    if not days:
        return 0
    import datetime
    today = datetime.date.today()
    d = today
    if d.isoformat() not in set(days):
        d -= datetime.timedelta(days=1)
    s = 0
    ds = set(days)
    while d.isoformat() in ds:
        s += 1
        d -= datetime.timedelta(days=1)
    return s

def main(argv=None):
    ap = argparse.ArgumentParser(description="Adaptive dual n-back trainer")
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--start-n", type=int, default=1)
    ap.add_argument("--fast", action="store_true", help="no delays (testing)")
    args = ap.parse_args(argv)
    hist = load_history()
    last_n = hist["sessions"][-1]["next_n"] if hist["sessions"] else args.start_n
    print(f"Starting dual n-back — N={last_n}, {args.trials} trials. "
          f"Streak: {streak_days(hist['sessions'])} days.")
    print("For each trial answer whether POSITION and LETTER match N steps back.")
    s = run_session(last_n, args.trials, delay=0 if args.fast else 1.6)
    s.pop("ts", None)
    s["ts"] = time.time()
    hist["sessions"].append({k: s[k] for k in
        ("n", "trials", "hits", "fa", "miss", "cr", "accuracy", "next_n", "ts")})
    save_history(hist)
    print(f"\nAccuracy: {s['accuracy']*100:.1f}%  (hits {s['hits']}, miss {s['miss']}, "
          f"false alarms {s['fa']})")
    if s["next_n"] > last_n:
        print(f"LEVEL UP — next session N={s['next_n']}")
    elif s["next_n"] < last_n:
        print(f"Level down — next session N={s['next_n']} (keep practicing)")
    else:
        print(f"Same level — next session N={s['next_n']}")
    print(f"Streak: {streak_days(hist['sessions'])} days")
    return 0

if __name__ == "__main__":
    sys.exit(main())
