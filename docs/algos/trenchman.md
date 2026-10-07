# Trenchman — dossier (scalp_b)

Wallet `Hw5UKBU5k3YudnGwaykj5E8cYUidNMPuEewRRar5Xoc7`. Algo: `gemtracker/algos/trenchman.py` (`name = "trenchman"`).

## Published (public, cited in gemtracker/elite.py: Kolscan / GMGN)
| stat | value |
|---|---|
| style | fast flip |
| median hold | 60 s |
| median entry mcap | $7.7k (~66 SOL, mid pump curve) |
| win rate | not published (lower than the scalpers per KOL-explorer; larger single trades) |

Public commentary: only the Kolscan listing; one 4.71 SOL sell seen in a public feed.

## Observed (fit span 20261007/17)
No Trenchman trades recorded yet (profiler: 0 trades).

## Inferred state machine
| step | rule | label |
|---|---|---|
| universe | pump or launchlab; age 15–180 s; mcap 45–150 SOL; >= 15 holders; top-10 <= 45 %; dev sold <= 50 % of what he bought; SOL-quoted | public mcap + our guess |
| entry | on a stranger's buy: >= 10 unique buyers, net >= +1 SOL and price change >= +20 % over 60 s | unknown (momentum heuristic) |
| size | 15 % of equity, <= 5 % price impact, <= 45 % exposure, <= 3 coins | our adaptation |
| adds | none | unknown / core limit |
| exits | 50 % out at +40 %; trail −20 % once +10 %; hard stop −20 %; flow stop (10 s); time stop 120 s | our adaptation (elite 60 s + latency margin) |
| risk | daily kill switch −15 %; never acts on Trenchman's own trades | our adaptation |

## Fit-span sanity (22 min of tape, 1 trial, no tuning)
| variant | return | trades | win | exits |
|---|---|---|---|---|
| trenchman | −16.2 % (kill switch hit) | 21 | 0.29 | flow 14, stop 4, trail 3, take 3 |
| random entry, same universe + exits (p = 0.44) | −16.0 % | 27 | 0.30 | |
| same signal, buy-and-hold 60 s | −9.7 % | 13 | 0.31 | |

Same as random; the flow stop fires on two thirds of trades, i.e. the entry chases a 60 s pump that is already reversing by the time the 2.5 s fill lands. Parameters to calibrate in Phase 2: `sig_min_trend`, `sig_min_buyers`, `flow_stop_ratio`, `flow_stop_secs`, `min_age_s`, `take_profit`, `time_stop_s`.
