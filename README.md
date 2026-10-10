# adaptive-nback

Adaptive **dual n-back** working-memory trainer (CLI, zero dependencies, MIT).

Existing open-source n-back tools are static demos (fixed N, no history) or
AGPL-licensed. This one adapts: **≥80% accuracy → N+1, <60% → N−1**, tracks
sessions and daily streaks in `~/.nback_history.json`.

## Usage

```bash
python -m nback                  # 20 trials, resumes your last N
python -m nback --trials 30 --start-n 2
```

Each trial shows a position on a 3×3 grid + a letter. Answer whether each
matches the stimulus **N steps back**.

## Test

```bash
python tests/test_nback.py
```

## License

MIT — see LICENSE.
