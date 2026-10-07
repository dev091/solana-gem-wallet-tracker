# Cented (scalp_a) - reconstruction dossier

Paper only. Code: `gemtracker/algos/cented.py`. Wallet (never a signal): `CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o`.
Labels: **public** / **observed** / **our adaptation** / **unknown**.

## 1. Published stats (public)
| Source | Figure |
|---|---|
| gemtracker/elite.py | scalper, median hold 12 s, median entry mcap $5,900 (~50 SOL), WR 0.53 |
| kucoin.com news / solana-trading.com | "7-second trader": $10M+, 308,666 trades in 357 days (~845/day, ~$33/trade), 62.3 % WR, 7 s median hold; a simulated copy with a 10 s delay returned -21.3 % |

## 2. Observed on the fit-span tape (20261007/17-21 UTC, ~0.13 h profiled)
| Item | Value |
|---|---|
| Trades | 35, all pump curve; entries at age 3-11 s, progress 0.20-0.32, 6-7 unique buyers/10 s, net10 +0.1..+9 SOL |
| Sizing | first clip 0.064 or 2.93 SOL; many 0.0053 SOL adds (bot-like) and a fixed 0.2444 SOL add ladder (x12) as price rises and on dips |
| Exits | scale-out: EkJECb sold at 56/65/95/119 s; EyuQgc one sell at 8.4 s at +23 % when the 10 s move was +40 %; first partial sell when 10 s net flow turned negative; 7cT1y9: 2.93 SOL in at 2.9 s, sold 1.79 SOL at 112 s (loss) |
| Caveat | ~8 min of tape; mcap_sol of some of these coins looks ~10x inconsistent with progress (open question for infra) |

## 3. Decision state machine
```
idle --[buyer burst on a 2-20 s old curve coin]--> pending buy --> held
held --[+25 %: sell 60 %, remainder trails 25 % from peak]--> partial
held/partial --[flow reversal after 5 s: sell 50 % then trail | -20 % hard stop | 60 s cap]--> flat
```
| Branch | Rule | Label |
|---|---|---|
| Entry | pump, create seen, age 2-20 s, progress <= 0.5, >= 5 unique buyers and >= 6 buys in 10 s, net10 >= 0.1, buys >= 1.5x sells, top10 <= 45 %, dev not sold | observed (age/progress/buyers) + our adaptation (thresholds) |
| Add ladder | observed (0.244 SOL steps) but **not implemented**: PaperSim drops a Buy on a coin already held | observed / blocked by core |
| Exits | 60 % at +25 %, remainder trails 25 % off peak; flow reversal after 5 s sells half; -20 % stop; 60 s cap | observed scale-out, our thresholds |
| Sizing / risk | 10 % of equity per clip, 5 % impact cap, <= 5 coins, <= 60 % deployed, -20 % daily kill | addendum |

## 4. Parameters to calibrate (Phase 2)
age_max_s, progress_max, min_unique_buyers_10s, min_buys_10s, tp1_mult, tp1_frac, trail_dd, flow_exit_frac, hard_stop, time_stop_s, size_frac.

## 5. Unknown
His 7 s median hold is faster than our public-feed latency (p90 2.0-2.6 s to see, +2.5 s to fill): the published copy-trade simulation at a 10 s delay lost 21 %. Expect behavioural fidelity, not his P&L. The add ladder needs core support (adds while holding).
