# Trunoest (scalp_a) - reconstruction dossier

Paper only. Code: `gemtracker/algos/trunoest.py`. Wallet (never a signal): `ardinRsN1mNYVeoJWTBsWeYeXvuR9UUDGMsCDKpb6AT`.
Labels: **public** / **observed** / **our adaptation** / **unknown**.

## 1. Published stats (public)
| Source | Figure |
|---|---|
| gemtracker/elite.py | scalper, median hold 21 s (longest of the group), median entry mcap $7,400 (~64 SOL), WR 0.62 |
| kolscan.io 30 d | #1, +$755.6K, WR 60 % |
| Prior research note | portfolio overlaps with the other top-3 wallets (coordinated network); no socials found |

## 2. Observed on the fit-span tape (20261007/17-21 UTC)
No trades recorded in the fit span yet (0 of ~83K decoded trades in the first 8 minutes). Everything below is a **public-only template**.

## 3. Decision state machine (template, unknown)
```
idle --[confirmed launch flow at age 5-60 s, >= 10 holders]--> held
held --[+30 % take profit | -15 % hard stop | flow reversal after 6 s | 40 s cap]--> flat
```
| Branch | Rule | Label |
|---|---|---|
| Entry | pump, create seen, age 5-60 s, mcap 40-200 SOL, progress <= 0.7, >= 6 unique buyers and >= 6 buys in 10 s, net10 >= 0.2, +5 % in 10 s, >= 10 holders, top10 <= 35 %, dev not sold | public (mcap band; longer hold => later, more confirmed entry); rest our adaptation |
| Exits | single exit at +30 %; -15 % stop; flow reversal (net10 < 0 and 10 s move < -8 %) after 6 s; 40 s cap (~2x his hold) | our adaptation |
| Sizing / risk | 12 % of equity, 5 % impact cap, <= 4 coins, <= 60 % deployed, -20 % daily kill | addendum |

## 4. Parameters to calibrate (Phase 2)
Everything; first wait for observed trades (re-run the profiler once his wallet shows on the tape).

## 5. Unknown
Venue mix, sizing, add/scale-out behaviour, what he filters on. The template is deliberately the most conservative of the group (holder floor, +5 % confirmation).
