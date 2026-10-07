# Mr. Frog — dossier (swing_base, Phase 1)

Paper only. Labels: **[public]** published / sourced, **[observed]** seen on our own tape,
**[our adaptation]** what we changed to survive our latency, **[unknown]** not knowable from public data.

## 1. Identity and published stats [public]

| item | value | source |
|---|---|---|
| wallet | `4DdrfiDHpmx55i4SPssxVzS9ZaKLb8qr45NKY9Er9nNh` | elite.py registry (KOL Explorer) |
| style | fast-flip | KOL Explorer 90 d |
| median hold | 120 s | KOL Explorer 90 d |
| median entry mcap | $4,200 (~36 SOL at $116) = Pump.fun launch mcap | KOL Explorer 90 d |
| win rate | 93.5 %, reliability 100/100 | KOL Explorer 90 d |
| public persona | @TheMisterFrog, influencer; no published method | web search, 2026-10-07 |

Reading of the stats [public, our inference]: a $4.2k median entry is the bonding-curve starting
mcap, so the median entry is within the launch block. A 93.5 % win rate on 2-minute holds is not
stock picking; it is being the first wave and selling into the second.

## 2. Observed on our tape [observed]

Fit span available so far: `data/tape/20261007/17.jsonl.gz` only (442 s). Profiler
(`data/profiles/Mr. Frog.trades.jsonl`, `.trips.jsonl`): 5 trades, 3 buys, 2 closed trips.

| trip | stake | coin state at entry | hold | result |
|---|---|---|---|---|
| 1 | 0.053 SOL | creation not seen (coin pre-dates recorder) | 43 s | +16 % (0.062 SOL out), mcap 695 SOL at exit, 13 buyers in 60 s |
| 2 | 2.963 SOL (3 SOL gross) | his buy is the first trade we receive; mcap 38.8 SOL at exit | 5.7 s | +11 % (3.30 SOL out) into 6 other buyers that arrived in those 5.7 s |
| 3 | 2.963 SOL | 850 s-old coin, 44 SOL mcap, no flow for 60 s, 16 sells / 2 buys, 1 holder | open at tape end | [unknown] relaunch / insider buy? |

Takeaways [observed]: fixed ~3 SOL stake (about 10 % of launch reserves: his buy *is* the first
pump), exit in seconds while followers still arrive, occasional small probes. The 5.7 s trip
contradicts the published 120 s median; n = 2, so neither number is settled.

## 3. Inferred decision state machine

```
SCAN   [public+observed] a coin he can hit in its launch block (creation seen, pump venue)
ARMED  [our adaptation]  age <= 20 s, mcap <= 60 SOL, >= 3 distinct buyers and >= 0.3 SOL net
                          inflow in 10 s, dev has not sold, not mayhem   (we can't be first, so we
                          require the first wave to be visible instead)
IN     [observed]        one attempt per coin, ~4 % of equity, liquidity-capped at 5 % impact
EXIT   [observed]        "wave over": held >= 6 s and 10 s net flow <= 0  -> sell all
       [public]          take-profit +35 % (full), hard stop -25 %, time stop 120 s
```

## 4. Parameters (`gemtracker/algos/mr_frog.py`, all class attributes)

| parameter | value | label | calibrate in Phase 2? |
|---|---|---|---|
| max_age_s | 20 | our adaptation | yes |
| max_entry_mcap_sol | 60 | public ($4.2k) + margin | yes |
| min_buyers_10s / min_net_sol_10s | 3 / 0.3 SOL | our adaptation | yes |
| max_dev_sold_frac | 0 | our adaptation | maybe |
| max_slippage | 0.40 | our adaptation | yes |
| fade_after_s / fade_net_sol_10s | 6 s / 0 | observed | yes |
| take_profit / stop_loss / max_hold_s | +35 % / -25 % / 120 s | public (hold), ours (levels) | yes |
| size_frac / max_price_impact | 0.04 / 0.05 | addendum | size only |
| max_exposure_frac / daily_kill_dd / max_positions | 0.40 / 0.15 / 8 | addendum risk rules | no (risk, not fit) |

## 5. Risk rules (Rahul's addendum)

Equity-fraction sizing with compounding; liquidity cap via `papersim.buy_out` (no buy moves price
> 5 %); hard stop per trade; daily kill switch (no new entries for the UTC day after -15 % from
start-of-day equity); exposure cap 40 % of equity; at most 8 positions.

## 6. Latency adaptation [our adaptation]

His edge is being in the launch block; our fills land 2.5 s after we decide, and we decide only
after the public feed shows the first buyers. We therefore buy the first wave instead of being
it, and sell when that wave fades. That is a different trade with the same shape; it should
not be expected to reproduce his win rate.

## 7. Phase 1 sanity replay (fit span 17 UTC, 442 s, $116/SOL, trial 1 = without wave-over exit)

| algo | buys | exits | rejects | median hold | pnl SOL | fees SOL | wins | return |
|---|---|---|---|---|---|---|---|---|
| mr_frog | 18 (18 coins) | stop 6, time 12 | 3 slippage | 120 s | -0.135 | 0.052 | 1/18 | -16.1 % |
| base_random | 63 | stop 13, time 44, tp 2 | 30 slippage | 120 s | -0.541 | 0.207 | 6/59 | -66.6 % |
| base_hold60 | 108 | time 108 | 11 | 60 s | -0.848 | 0.313 | 12/108 | -99.7 % |
| base_elite_copy | 26 | elite sold 19, stop 5, time 1 | 4 | 10 s | -0.293 | 0.077 | 2/25 | -33.3 % |

Difference from base_random: +50 pp; from base_hold60: +84 pp; both still losses. Fixed tx fee
(0.001 SOL per side) is 2.6 % of a 0.04 SOL stake each way: at $100 equity the fee model alone
eats ~5 % per round trip.

Trial 2 (same span, with the observed wave-over exit): 21 buys on 21 coins, exits wave-over 13 /
stop 7 / take-profit 1, 2 slippage rejects, median hold 7.8 s, pnl -0.142 SOL (-16.4 % of the
0.862 SOL start), fees 0.060 SOL, 1/21 wins. The exit shape now matches the observed 6-45 s
holds, but the loss is unchanged: the losses are post-fill drift plus fees, not hold time.

## 8. Unknowns / open questions

- [unknown] how he is in the launch block (bundler, private RPC, creator link) — not public.
- [unknown] trip 3 (buying a dead 850 s-old coin with 3 SOL).
- Core: `TokenState.window()` counts every wallet, so the target's own buy counts as one of the
  "distinct buyers" on the tape; excluding named wallets from the counts needs a market.py change.
- Phase 2: shorten max_hold toward the observed 6-45 s band? Only with a full fit day and a
  counted trial.

Trial count for this trader: 2 fit-span replays (trial 1 initial parameters, trial 2 after adding
the observed wave-over exit). No parameter was searched.
