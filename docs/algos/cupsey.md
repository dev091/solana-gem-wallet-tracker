# Cupsey — dossier (scalp_b)

Wallet `2fg5QD1eD7rzNNCsvnhmXFm5hqNgwTTG8p7kQ6f3rx6f`. Algo: `gemtracker/algos/cupsey.py` (`name = "cupsey"`).

## Published (public, cited in gemtracker/elite.py: Kolscan / GMGN)
| stat | value |
|---|---|
| style | scalper |
| median hold | 17 s |
| median entry mcap | $10.3k (~89 SOL at 116 $/SOL, ~progress 0.6 on the pump curve) |
| win rate | 0.42 |

Public commentary (solana-trading / KOL-explorer write-ups fetched earlier this session): high-frequency launch sniper, a fixed ~3 SOL per coin within minutes of launch, exits in seconds to minutes, small capped chase adds, flow-based rather than chart-based.

## Observed (fit span 20261007/17, profiler: 12 trades, 2 round trips, win 0.0, hold p50 4.9 s)
- 2.53 SOL into a PumpSwap pool 25 s after migration; state before the buy: 3 unique buyers and +3 SOL net in 10 s, price +20 % over 60 s. Cut at −24 % after 43 s when the 10 s window turned all-sell.
- A bonding-curve trade sold in 4 chunks within 5 s at 0.92x.
- Cented was already in before one entry (single observation: not used as a condition).

## Inferred state machine
| step | rule | label |
|---|---|---|
| universe | pump or pumpswap; curve age <= 120 s or pool age <= 120 s; mcap 40–400 SOL; SOL-quoted only | observed + public |
| entry | on a stranger's buy: >= 3 unique buyers and net >= +0.5 SOL in 10 s, 60 s price change > 0 | observed (1 trade) |
| size | 15 % of equity (cash + marked positions), capped so the buy moves price <= 5 %; <= 45 % exposure, <= 3 coins | our adaptation (elite: fixed ~3 SOL) |
| adds | none (sim rejects a second buy on an open position) | unknown / core limit |
| exits | 50 % out at +25 %; trail −15 % from peak once +10 %; hard stop −20 %; flow stop (sells >= 2x buys and net < 0 in 10 s); time stop 60 s | our adaptation (elite median 17 s does not survive 2.5 s latency) |
| risk | daily kill switch at −15 % of UTC day-start equity; never acts on Cupsey's own trades | our adaptation |

## Fit-span sanity (22 min of tape, 1 trial, no tuning)
| variant | return | trades | win | exits |
|---|---|---|---|---|
| cupsey | −15.4 % (kill switch hit) | 6 | 0.33 | trail 3, flow 2, take 1, stop 1 |
| random entry, same universe + exits (p = 0.36) | −11.7 % | 20 | 0.25 | |
| same signal, buy-and-hold 60 s | −25.7 % | 14 | 0.29 | |

No edge over the random baseline on this span; the signal fires on 36 % of universe-passing buys, which is far too permissive. Parameters to calibrate in Phase 2: `sig_min_buyers`, `sig_min_net_sol`, `sig_min_trend`, `max_age_s`, `min_mcap_sol`, `take_profit`, `trail_from_peak`, `time_stop_s`.
