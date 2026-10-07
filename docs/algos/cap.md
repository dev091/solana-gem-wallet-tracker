# Cap — dossier (scalp_b)

Wallet `CAPn1yH4oSywsxGU456jfgTrSSUidf9jgeAnHceNUJdw`. Algo: `gemtracker/algos/cap.py` (`name = "cap"`).

## Published (public, cited in gemtracker/elite.py: Kolscan / GMGN)
| stat | value |
|---|---|
| style | fast flip |
| median hold | 59 s |
| median entry mcap | $17.6k (~152 SOL: last quarter of the pump curve or a fresh PumpSwap pool) |
| win rate | not published; recent 7-day drawdown (−$40.1k) per KOL-explorer |

Public commentary: only the Kolscan listing; the high entry mcap is what separates him from the other three.

## Observed (fit span 20261007/17)
No Cap trades recorded yet (profiler: 0 trades).

## Inferred state machine
| step | rule | label |
|---|---|---|
| universe | pump with progress >= 0.55, or pumpswap pool <= 120 s old; mcap 100–400 SOL; >= 30 holders; top-10 <= 35 %; SOL-quoted | public mcap + our guess |
| entry | on a stranger's buy: mcap >= 90 % of ATH, >= 15 unique buyers and net >= +3 SOL in 60 s, last 10 s net positive | unknown (breakout heuristic) |
| size | 15 % of equity, <= 5 % price impact, <= 45 % exposure, <= 3 coins | our adaptation |
| adds | none | unknown / core limit |
| exits | 50 % out at +30 %; trail −15 % once +10 %; hard stop −15 %; flow stop (10 s); time stop 120 s | our adaptation (elite 59 s + latency margin) |
| risk | daily kill switch −15 %; never acts on Cap's own trades | our adaptation |

## Fit-span sanity (22 min of tape, 1 trial, no tuning)
| variant | return | trades | win | exits |
|---|---|---|---|---|
| cap | −16.3 % (kill switch hit) | 3 | 0.00 | stop 2, flow 1 |
| random entry, same universe + exits (p = 0.25) | −15.4 % | 4 | 0.00 | |
| same signal, buy-and-hold 60 s | −30.0 % | 8 | 0.25 | |

Three trades, all stopped out: buying at the ATH of a late curve with a 2.5 s fill is buying the top of a migration spike. Parameters to calibrate in Phase 2: `sig_ath_frac`, `min_progress`, `sig_min_net_sol`, `max_loss_per_trade`, `max_pool_age_s`, `time_stop_s`; also test the PumpSwap-only variant (5.5 s latency) separately from the late-curve variant.
