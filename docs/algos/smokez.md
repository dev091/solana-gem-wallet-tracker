# Smokez — dossier (swing_base, Phase 1)

Paper only. Labels: **[public]**, **[observed]**, **[our adaptation]**, **[unknown]**.

## 1. Identity and published stats [public]

| item | value | source |
|---|---|---|
| wallet | `5t9xBNuDdGTGpjaPTx6hKd7sdRJbvtKS8Mhq6qVbo8Qz` | elite.py registry (KOL Explorer) |
| style | fast-flip | KOL Explorer 90 d |
| median hold | 120 s | KOL Explorer 90 d |
| median entry mcap | $16,000 (~138 SOL at $116) | KOL Explorer 90 d |
| win rate | 38 %, median trade 0.84x, reliability 60/100, "streaky" | KOL Explorer 90 d |
| public persona | @SmokezXBT, KOL; no published method | web search, 2026-10-07 |

Reading [public, our inference]: $16k is a fifth of the way up the Pump.fun curve, so he buys
coins that already move, not launches. Profitable at a 38 % win rate with a 0.84x median trade
means many small losses and a few large winners: a tight stop and a trailing exit, not a fixed
target.

## 2. Observed on our tape [observed]

None yet: 0 trades in the 442 s fit span (`data/profiles/summary.json`, "Smokez": trades 0).
Everything below is inferred from the published numbers until a full fit day exists.

## 3. Inferred decision state machine

```
SCAN   [public]          Pump.fun curve coin whose creation we saw, not migrated
ARMED  [public+ours]     age 20 s .. 30 min, mcap 90-400 SOL, price +20 % over 60 s,
                          >= 4 distinct buyers in 10 s, >= 1 SOL net inflow in 60 s,
                          top-10 holders <= 45 %, dev sold <= 50 % of its buy
IN     [ours]            8 % of equity, liquidity-capped; re-check a coin at most every 60 s
EXIT   [public shape]    hard stop -15 %; sell half at +50 %; trailing stop 20 % from peak once
                          +30 %; time stop 240 s
```

## 4. Parameters (`gemtracker/algos/smokez.py`)

| parameter | value | label | calibrate? |
|---|---|---|---|
| min_age_s / max_age_s | 20 / 1800 | our adaptation | yes |
| min_entry_mcap_sol / max_entry_mcap_sol | 90 / 400 | public ($16k) + band | yes |
| min_change_60s / min_buyers_10s / min_net_sol_60s | 0.20 / 4 / 1 SOL | our adaptation | yes |
| max_top10_share / max_dev_sold_frac | 0.45 / 0.5 | our adaptation | maybe |
| stop_loss / take_profit (tp_fraction) | 0.15 / 0.50 (half) | public shape, our levels | yes |
| trail_arm / trail_drop / max_hold_s | 0.30 / 0.20 / 240 s | public shape, our levels | yes |
| size_frac / max_price_impact | 0.08 / 0.05 | addendum | size only |
| max_exposure_frac / daily_kill_dd / max_positions | 0.50 / 0.15 / 6 | addendum risk rules | no |

## 5. Risk rules (addendum)

As for the group: equity-fraction compounding size, 5 % impact cap, hard stop, daily -15 % kill
switch per UTC day, 50 % exposure cap, 6 positions.

## 6. Latency adaptation [our adaptation]

Momentum measured on the received feed is 2.5 s stale; the fill lands another 2.5 s later. The
tight stop therefore sees post-latency drift immediately (observed in the sanity replay: median
hold 4.6 s, 10 of 19 exits were stops). The time stop is longer than his median hold because
late fills need the winners to pay for the stops.

## 7. Phase 1 sanity replay (fit span 17 UTC, 442 s, $116/SOL, trial 1)

| algo | buys | exits | rejects | median hold | pnl SOL | fees SOL | wins | return |
|---|---|---|---|---|---|---|---|---|
| smokez | 19 (14 coins) | stop 10, trail 5, time 3, tp 1 | 2 slippage | 4.6 s | -0.099 | 0.068 | 8/19 | -11.3 % |
| base_random | 63 | stop 13, time 44, tp 2 | 30 | 120 s | -0.541 | 0.207 | 6/59 | -66.6 % |
| base_hold60 | 108 | time 108 | 11 | 60 s | -0.848 | 0.313 | 12/108 | -99.7 % |
| base_elite_copy | 26 | elite sold 19, stop 5, time 1 | 4 | 10 s | -0.293 | 0.077 | 2/25 | -33.3 % |

Difference from base_random: +55 pp; from base_hold60: +88 pp; still a loss. Fees were 69 % of
the loss: 38 fills at 0.001 SOL fixed tx fee on 0.07 SOL stakes.

## 8. Unknowns / open questions

- [unknown] his actual entry trigger (chart pattern, social signal, or group calls) and his
  stop discipline; the published 0.84x median trade is consistent with but does not prove a
  tight stop.
- The -15 % stop fires on post-fill drift within seconds; whether that is the right stop or
  latency noise is a Phase 2 question (counted trials on a full fit day).
- Phase 2 needs his first observed trades to anchor the mcap band and hold time.

Trial count for this trader: 1 fit-span replay. No parameter was searched.
