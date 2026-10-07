# Decu (scalp_a) - reconstruction dossier

Paper only. Code: `gemtracker/algos/decu.py` (parameters are class attributes on `Decu`; template in `_scalp_a_base.py`).
Wallet (never a signal): `4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9`. Labels: **public** / **observed** / **our adaptation** / **unknown**.

## 1. Published stats (public)
| Source | Figure |
|---|---|
| gemtracker/elite.py (KOL Explorer 90 d) | scalper, median hold 14 s, median entry mcap $8,200 (~70 SOL at $116), WR 0.64 |
| kolexplorer.com/kol/decu | +$983K 90 d, 63.9 % WR, 11,883 positions, 14 s median hold |
| x.com/notdecu (own thread) | checks name, ticker, dev wallet, holders before entry; Axiom-affiliated |
| Nansen label | "New Token Specialist" |

## 2. Observed on the fit-span tape (20261007/17-21 UTC; profiler run at ~0.13 h of tape)
| Item | Value |
|---|---|
| Trades | 6 (all PumpSwap, migrated coins); 2 closed trips, both losers (multiple ~0.81) |
| Entry state | price 44-58 % below ATH, net60 ~ -41 SOL, 10 s sells >> buys, 1-2 unique buyers/10 s |
| Sizes | 0.025 / 0.25 / 4.95 SOL buys; single sell per trip after ~16 s |
| Caveat | n=6 in 8 minutes of tape; one sell closed a position opened before recording |

The observed behaviour (buying a post-migration flush) does not match his published "new token" profile; the 90-day stats say most of his 11.9K positions are fresh launches we have not yet seen him trade on this tape.

## 3. Decision state machine
```
idle --[fresh-launch flow (public band) | post-migration flush (observed)]--> pending buy
pending buy --[fill at arrival, slippage <= 25 %]--> held
held --[+25 % take profit | -15 % hard stop | flow reversal after 5 s | 30 s time stop]--> flat
flat --[120 s cooldown, <= 2 entries per coin]--> idle
```
| Branch | Rule | Label |
|---|---|---|
| Fresh-launch flow | pump curve, create seen, age 3-45 s, mcap 35-150 SOL, progress <= 0.6, >= 6 unique buyers and >= 6 buys in 10 s, net10 >= 0.3 SOL, +10 % in 10 s, buys >= 1.5x sells, top10 <= 35 %, dev has not sold, not mayhem | public band + our adaptation (flow filters are ours) |
| Post-migration flush | pumpswap, price <= 0.6x ATH, >= 10 SOL sold in 60 s, net60 < 0, age <= 30 min; half size | observed (n=3 buys, both closed trips lost) |
| Exits | +25 % all out; -15 % hard stop; after 5 s, net10 < 0 and 10 s move < -8 %; 30 s cap | our adaptation (his 14 s hold does not survive 2.5-5.5 s latency) |
| Sizing | 15 % of equity (7 % for flush buys), <= 5 % price impact via constant-product cap, <= 60 % of equity deployed, <= 4 coins | addendum |
| Risk | hard stop 15 %/trade; no new entries for the UTC day after -20 % from day-start equity | addendum |

## 4. Parameters to calibrate (Phase 2)
age band, mcap band, min_unique_buyers_10s, min_net_sol_10s, min_price_change_10s, tp1_mult, hard_stop, time_stop_s, dip_from_ath, dip_min_sell_sol_60s, size_frac. Count every trial.

## 5. Unknown
Whether his fresh-launch entries key on name/ticker (he says they do; we cannot score that), his real stop rule, whether the flush buys hedge an existing bag.
