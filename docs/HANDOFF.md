# HANDOFF: live state of the work

**Owner: Codex** (handed over by Claude on 2026-10-07 at 10:24 PM ET, at Rahul's request).
Read `AGENTS.md` first. Update this file at the end of every work block (see the bridge rules in AGENTS.md).

## Now (2026-10-07, 10:24 PM ET)
### Live processes (started by Claude; leave them running)
| What | PIDs | Notes |
|---|---|---|
| Recorder | 3604 (launcher), 23652 (child, ~300 MB) | Started 8:08 PM ET. Runs the old 16 algos plus 3 baselines, 19 in all. Latency 2.5 s (pumpswap 5.5 s). |
| Dashboard | 32604, 16532 (conhost 19576) | http://127.0.0.1:8766 |

- **Live P&L.** Every algo is negative. The best are cap, trunoest_hold and cupsey at about -15%. The baselines are at -64% to -99%.
- **Why the old algos are still live.** They stay until replacements pass the floor; nothing has passed yet.

### Elite20 research (protocol: `data/research/elite20/BRIEF.md`)
The families are:
- pc_: pump curve;
- ps_: PumpSwap after graduation;
- el_: elite-derived;
- mc_: established-token swing.

| Family | Status | Checkpoint |
|---|---|---|
| `pc_` pump curve, pre-graduation (7 slots) | Wave 1: 0 of 45 trials passed (30 beat their in-cell random baseline, all negative in absolute terms). Wave 2: 14 trials pre-registered (organic-flow momentum, holder breadth, big-move-only; rugcheck mandatory), N_trials = 59. `holders.py` features are done for all 17 FIT days; `screen_w2.py` has **not** run. Next: screen_w2, then `report.py --tag w2 --n-trials 59`; freeze and run histrun VAL only for cells positive at 2.5 s with CI, else close 0/7. No third wave. | `data/research/elite20/pc/HANDOFF.md`, `data/history/orig/` |
| `ps_` PumpSwap, post-graduation (7) | Data route: BigQuery `Token Transfers` rebuilds swaps (~20-26 GB per UTC day); `Instructions` has no event CPIs, so `scripts/ps/bq_pumpswap.py` is obsolete for events. Approved budget ≤ 380 GB, VAL days first; stop if the month would pass 800 GB; ledger in `bq_ledger.jsonl` (not created yet). Token Transfers spend so far: 0 GB; month-to-date billed 26.11 GB. The 1-hour 08-21 validation pull (≤ 1.5 GB) has **not** run, so the reconstruction is unvalidated. Next: dataset `ps` plus `pool_atas`, dry-run, validation, then the per-day fetch (handoff section 7). | `data/research/elite20/ps/HANDOFF.md`, `scripts/ps/` |
| `el_` elite-derived (6) | **0 of 8.** Every elite slice is negative on FIT once age ≥ 30 s and the 3 s delay apply. 8 FIT-failure cards are in `cards/`; VAL was never spent. | `data/research/elite20/el/HANDOFF.md` |
| `mc_` (new, replaces el_'s slots) | Planned only: swing established SPL tokens on Raydium, Orca and Meteora, hours horizon, where latency matters little. Point-in-time universe comes from ps_'s per-(mint, hour) aggregates. | `data/research/elite20/mc/HANDOFF.md` |

**Honest outlook:** zero algos have passed the floor so far. The deliverable may well be fewer than 20.

**Stale HEAVY.lock.** `data/research/elite20/HEAVY.lock` says `agent=fable-orig pid=114150`. That PID is dead (checked 10:24 PM ET) and no research process of Claude's is running. The pc_ agent was refused deleting it, so Claude left it in place. Rahul may delete it; otherwise the new owner takes it over (rewrite it with your own agent, PID and ET time) before the next heavy job.

All three research agents stopped by 10:23 PM ET. No BigQuery job is in flight and nothing of theirs was committed.

### Done and committed
- **291c8e1 rugcheck.** One fail-closed rug filter (`gemtracker/rugcheck.py`, 12 tests): age, depth versus our size, top-10, dev bag, launch bundles, dev dumping, and other-DEX token/LP/sellability facts through `Meta`. Plus the tail-aware size `risk_size_frac`.
- **be15db3 and c0b6a8b dashboard.** The live paper desk, and the VAL columns from the cards.
- **Uncommitted** (untracked research): `data/research/`, `scripts/grad/`, `scripts/ps/`.

## Next (in order)
1. Read the four family checkpoints above, then resume the families one at a time, heavy jobs serialized under HEAVY.lock.
2. **ps_:** run the VAL Token Transfers pull within budget, and in the same scan write `data/research/elite20/bq_mint_hourly/<utc_day>.parquet` (feeds mc_). Then FIT and VAL the ps_ ideas.
3. **pc_:** finish wave 2 (≤ 20 trials). Run VAL only for a candidate whose FIT is positive.
4. **mc_:** build the universe, FIT, then freeze and run VAL once.
5. **Swap** (once at least one algo passes the floor):
   - remove the old algo files (listed in AGENTS.md) and port the base tests in `test_algos_elite5`, `test_algos_review_fixes`, `test_algos_scalp_a`, `test_algos_scalp_b` and `test_algos_swing_base` to stubs;
   - create `data/paper/recorder/STOP`;
   - restart the recorder at BelowNormal with `--algos <passing>,base_random`;
   - run the full suite;
   - check the dashboard;
   - commit;
   - give Rahul an honest ET report.
6. **Later:** a `jup` live venue (DexScreener plus read-only Jupiter quotes) and a `Meta` fetcher (RPC mint/freeze authority, getTokenLargestAccounts, Token-2022 extensions, LP lock, round-trip quote). Possibly attach the LaunchLab tx signer so those coins become buyable.

## Open questions for Rahul
- If nothing passes the floor, should the old algos keep running, or be stopped to save the machine?
