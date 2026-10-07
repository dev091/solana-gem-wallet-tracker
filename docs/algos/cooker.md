# Cooker (@CookerFlips) — dossier (scalp_b)

Wallet `8deJ9xeUvXSJwicYptA9mHsU2rN2pDx37KWzkDkEXhU6`. Algo: `gemtracker/algos/cooker.py` (`name = "cooker"`).

## Published (public, cited in gemtracker/elite.py: Kolscan / GMGN)
| stat | value |
|---|---|
| style | scalper, fastest on the board |
| median hold | 9 s (mean 5.8 h: "forgotten bags") |
| median entry mcap | $6.3k (~54 SOL, first fifth of the pump curve) |
| win rate | 0.71 |

Public commentary: high-volume, thin-margin flips; no description of a trigger anywhere public.

## Observed (fit span 20261007/17)
No Cooker trades recorded yet (profiler: 0 trades). Everything below the "published" row is therefore unknown or our guess.

## Inferred state machine
| step | rule | label |
|---|---|---|
| universe | pump only, creation seen (exact age), age <= 30 s, mcap 35–120 SOL, top-10 holders <= 50 %, dev has not sold, SOL-quoted | public mcap + our guess |
| entry | on a stranger's buy: >= 4 unique buyers in 5 s and net >= +0.5 SOL in 10 s | unknown (burst heuristic) |
| size | 12 % of equity, <= 5 % price impact, <= 36 % exposure, <= 3 coins | our adaptation |
| adds | none | unknown / core limit |
| exits | all out at +20 %; trail −10 % once +8 %; hard stop −12 %; flow stop (5 s); time stop 25 s | our adaptation (elite 9 s hold is not reachable at 2.5 s latency) |
| risk | daily kill switch −12 %; never acts on Cooker's own trades | our adaptation |

## Fit-span sanity (22 min of tape, 1 trial, no tuning)
| variant | return | trades | win | exits |
|---|---|---|---|---|
| cooker | −15.2 % (kill switch hit) | 7 | 0.00 | stop 4, take 1, flow 1, time 1 |
| random entry, same universe + exits (p = 0.49) | −16.6 % | 7 | 0.00 | |
| same signal, buy-and-hold 60 s | −14.0 % | 3 | 0.00 | |

Indistinguishable from random on this span; every closed trade lost. The "take" exit that still lost shows the +20 % target is inside the fee + latency + slippage cost of a 30 s old curve. Parameters to calibrate in Phase 2: `sig_min_buyers`, `sig_secs`, `max_age_s`, `take_profit`, `max_loss_per_trade`, `time_stop_s`; also decide whether the 71 % published win rate is reproducible at all without sub-second execution.
