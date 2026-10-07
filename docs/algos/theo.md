# Theo (scalp_a) - reconstruction dossier

Paper only. Code: `gemtracker/algos/theo.py`. Wallet (never a signal): `Bi4rd5FH5bYEN8scZ7wevxNZyNmKHdaBcvewdPFxYdLt`.
Labels: **public** / **observed** / **our adaptation** / **unknown**.

## 1. Published stats (public)
| Source | Figure |
|---|---|
| gemtracker/elite.py | scalper, median hold 17 s, median entry mcap $4,800 (~41 SOL; earliest entries of the group), WR 0.50 |
| kolscan.io | buys of ~3-7 SOL, holds from seconds to ~15 min, trip ROI -83 %..+187 %; no socials found |

## 2. Observed on the fit-span tape (20261007/17-21 UTC, ~0.13 h profiled)
| Item | Value |
|---|---|
| Trade 1 | 0.0056 SOL at age 4.6 s on a strong launch (35 buys, 15 unique buyers/10 s, +57 % in 10 s); sold in two tranches at 25-28 s when net10 < 0 and the 10 s move was -35 %; multiple 7.5 on a tiny size |
| Trade 2 | 0.108 SOL at age 203 s on an established coin (progress 0.88, 193 holders) where Cented and Cupsey were already in (net60 +0.34, +40 % in 60 s); sold 38 s later (+4 %) |
| Caveat | n=5 trades; the "follows other elites" read is n=1 |

## 3. Decision state machine
```
idle --[buyer burst at age 2-30 s | >= 2 OTHER elites in, 60 s move >= +20 %, age <= 300 s]--> held
held --[+60 %: sell half, rest trails 25 %]--> partial
held/partial --[flow reversal after 5 s (net10 < 0, 10 s move < -15 %): sell half then trail | -25 % stop | 45 s cap]--> flat
```
| Branch | Rule | Label |
|---|---|---|
| Buyer burst | pump, create seen, age 2-30 s, progress <= 0.6, >= 8 unique buyers and >= 10 buys in 10 s, net10 >= 0.15, +20 % in 10 s, top10 <= 30 %, dev not sold | observed (trade 1) + our thresholds |
| Follow elites | >= 2 elites other than Theo in st.elite_buys, age <= 300 s, not migrated, progress <= 0.97, 60 s move >= +20 % and net60 >= 0 | observed n=1; the dossier shows the target conditioning on it |
| Exits | two tranches on flow reversal (observed) with our thresholds; +60 % half; -25 % stop; 45 s cap | observed / our adaptation |
| Sizing / risk | 12 % of equity, 5 % impact cap, <= 4 coins, <= 60 % deployed, -20 % daily kill | addendum |

## 4. Parameters to calibrate (Phase 2)
min_unique_buyers_10s, min_buys_10s, min_price_change_10s, follow_elites_min, follow_min_price_change_60s, flow_exit_price_change_10s, tp1_mult, hard_stop, time_stop_s.

## 5. Unknown
Whether he copies other elites or saw the same signal; his stop rule; whether the Kolscan 3-7 SOL buys are a different mode than the 0.0056 SOL probe seen here.
