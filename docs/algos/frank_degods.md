# Frank degods — dossier (swing_base, Phase 1)

Paper only. Labels: **[public]**, **[observed]**, **[our adaptation]**, **[unknown]**.

## 1. Identity and published stats [public]

| item | value | source |
|---|---|---|
| wallet | `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ` | elite.py registry (KOL Explorer) |
| style | swing / position | KOL Explorer 90 d |
| median hold | 9,360 s (2.6 h) | KOL Explorer 90 d |
| median entry mcap | $497,000 (~4,300 SOL at $116) | KOL Explorer 90 d |
| win rate | not published | — |
| public persona | Frank (Rohun Vora), DeGods founder; early entries that later ran, adds on dips, fast block selling into strength, sold > $1M of memes on 2026-10-07 | Lookonchain / FOMO leaderboard / DL News, web search 2026-10-07 |

Reading [public, our inference]: $497k is far past Pump.fun migration (~$69k), so his coins
trade on PumpSwap with an established holder base; a 2.6 h hold is a swing on sustained flow.

## 2. Observed on our tape [observed]

None yet: 0 trades in the 442 s fit span. A 2.6 h-hold trader may show a handful of trades per
day; the dossier needs several fit days before "observed" means anything.

## 3. Inferred decision state machine

```
SCAN   [public]          migrated coin on PumpSwap, mcap 1,500-12,000 SOL (band around $497k;
                          the upper bound is also a sanity cap, see unknowns)
ARMED  [ours]            >= 40 trades seen, >= 60 holders seen, top-10 <= 35 %, and over 60 s:
                          >= 8 distinct buyers, >= 3 SOL net inflow, price up >= 3 %
IN     [public]          concentrated: 20 % of equity, at most 3 positions, 60 % exposure
ADD    [public]          add on a dip while flow stays positive  -> BLOCKED by papersim.submit
                          (a Buy on an open or pending mint is dropped); add_on_dip = False
EXIT   [public shape]    hard stop -30 %; sell half at 2x; trailing 30 % from peak once +60 %;
                          "flow breakdown": under water and 60 s net flow <= -5 SOL -> sell all;
                          time stop 3 h
```

## 4. Parameters (`gemtracker/algos/frank_degods.py`)

| parameter | value | label | calibrate? |
|---|---|---|---|
| min_entry_mcap_sol / max_entry_mcap_sol | 1,500 / 12,000 | public ($497k) + band | yes |
| min_buyers_60s / min_net_sol_60s / min_change_60s | 8 / 3 SOL / 0.03 | our adaptation | yes |
| min_trades_seen / min_holders / max_top10_share | 40 / 60 / 0.35 | our adaptation | yes |
| stop_loss / take_profit (half) / trail_arm / trail_drop | 0.30 / 1.00 / 0.60 / 0.30 | public shape, our levels | yes |
| breakdown_net_sol_60s | -5 SOL | our adaptation | yes |
| max_hold_s | 3 h | public (2.6 h median) | yes |
| retry_after_s | 30 | ours (cost control) | no |
| size_frac / max_price_impact | 0.20 / 0.05 | addendum | size only |
| max_exposure_frac / daily_kill_dd / max_positions | 0.60 / 0.15 / 3 | addendum risk rules | no |

## 5. Risk rules (addendum)

Equity-fraction compounding size, 5 % impact cap (PumpSwap pools are deep, the cap rarely binds),
hard stop, daily -15 % kill switch, 60 % exposure cap, 3 positions.

## 6. Latency adaptation [our adaptation]

PumpSwap intents land 5.5 s after the decision; on a 2.6 h swing that is noise for entries but
matters for the breakdown exit, which reacts to a full minute of selling rather than a tick.
The published "add on dips" cannot be simulated (see core changes).

## 7. Phase 1 sanity replay (fit span 17 UTC, 442 s, $116/SOL, trial 1)

| algo | buys | exits | rejects | pnl SOL | fees SOL | wins | return |
|---|---|---|---|---|---|---|---|
| frank_degods | 6 (2 coins, re-entries) | flow breakdown 5 | 0 | -0.103 realized | 0.020 | 0/5 | +1.1 % (one open position marked up) |
| base_random | 63 | stop 13, time 44, tp 2 | 30 | -0.541 | 0.207 | 6/59 | -66.6 % |
| base_hold60 | 108 | time 108 | 11 | -0.848 | 0.313 | 12/108 | -99.7 % |
| base_elite_copy | 26 | elite sold 19, stop 5, time 1 | 4 | -0.293 | 0.077 | 2/25 | -33.3 % |

It trades, but 442 s is 5 % of its intended hold; the five closes were all breakdown exits on
two coins. Nothing about a 3 h swing can be judged on this span.

## 8. Unknowns / open questions

- [unknown] how he finds coins early (network, DMs) — only the on-chain footprint is public.
- Core (market.py): PumpSwap trades for pools whose creation was not seen default to
  PUMP_SUPPLY, so mcap is mis-scaled for 30k of 45k pumpswap rows in hour 17 (mcap > 1e6 SOL).
  The 12,000 SOL upper bound is a stop-gap filter; a real fix needs supply/decimals per pool.
- Core (papersim.submit): adds to an open position are dropped, so the "add on dips" leg is off.
- Re-entries: with retry_after_s = 30 the algo re-bought the same coin after a breakdown exit;
  a cooldown per coin after an exit is a candidate Phase 2 rule (counted).

Trial count for this trader: 1 fit-span replay. No parameter was searched.
