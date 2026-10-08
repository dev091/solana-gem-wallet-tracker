# solana-tracker: shared brief for Codex and Claude

Both agents read this file first. Codex CLI loads it automatically; Claude Code loads it through `CLAUDE.md`.
The current state and next steps are in `docs/HANDOFF.md`. Read that second.

## What this is
This is a **paper-trading** desk for Solana meme coins.
- The live recorder streams pump.fun curve, PumpSwap and LaunchLab trades over free public WebSockets.
- Algos trade those streams in paper through `papersim`, with fees and live latency.
- A local dashboard shows the results.

Owner: Rahul. He writes Hinglish. Reply to him short, result first, and give every time in ET.

## Goal (Rahul, 2026-10-07)
- **Daily target.** $100 start per algo, 100% compounding, at least $1.5k/day by 2026-12-07. That needs about +8.8%/day geometric.
- **Beat Decu.** The metric is return per SOL over the same ET days; see `-m gemtracker.scoreboard`.
- **Current ask.** Replace the current algos, which Rahul calls useless (0 green ET-days), with up to 20 new elite algos, live on the dashboard.
- **Universe.** Any Solana coin on any DEX, not only pump.fun.
- **Risk.** Avoid rugs: minimum risk, maximum profit.
- **Delivery.** Ship only what passes the VAL gates. "Kamzor niklega to hatao": a weak algo is removed, never patched on VAL.
- **What "elite" means.** An elite algo is that trader's own reverse-engineered decision function. It is never a copy bot that follows a wallet.

## Hard rules (never break)
- **Paper only.**
  - No orders, wallets, private keys, seed phrases or swap transactions.
  - Jupiter quotes are read-only.
  - No real money, ever.
  - The Polymarket bot runs only when Rahul says so.
- **Free tools only.**
  - Allowed: public Solana RPC and WebSockets, GeckoTerminal, DexScreener, pump.fun boards, HF and Kaggle, and BigQuery within the free tier (≤ 1 TiB/month; log every query in `data/research/elite20/bq_ledger.jsonl`).
  - Not allowed: Helius, paid PumpPortal, NoLimitNodes, Bitquery.
  - On a 413, a 429 or any other block: wait. Never rotate IPs or keys, and never route around the block.
- **Secrets.**
  - They live only in the git-ignored `data/secrets/`.
  - Never print, paste or ask for them.
  - Never search `C:\Users` broadly.
- **HOLDOUT.** Never load any ET day on or after 2026-09-05, from any source, API calls included.
  - GeckoTerminal: `before_timestamp` ≤ 2026-09-05 00:00 ET.
  - BigQuery: max ts < 2026-09-05 04:00 UTC, asserted on every pull.
- **Shared machine.** It has 15.7 GB of RAM, shared with Rahul's Polymarket bots.
  - Run one heavy job (over 1 GB) at a time, holding `data/research/elite20/HEAVY.lock` (`agent=.. pid=.. started ..ET`).
  - Each job stays ≤ 2.5 GB, at BelowNormal priority, one day per pass, float32.
  - Start only when at least 3 GB is free.
- **Process kills.** Never kill by name or filter (`taskkill /IM`, filtered Stop-Process). Kill only the exact PIDs you started. For anything else, give Rahul `taskkill /F /T /PID <n>`.
- **Time.** Git Bash `TZ=...` gives wrong ET. Use `powershell -NoProfile -c "Get-Date -Format 'h:mm tt'"`.
- **Quality.**
  - Never skip tests or verification.
  - Report honestly, failures included.
  - Don't ask about routine steps. Ask only about money, irreversible actions or publishing.
- **Git.**
  - Work on branch `claude/solana-gem-wallet-tracker`. Make small, tested commits.
  - Never push or force-push without Rahul.

## Run it
Python is `D:\DeveloperStorage\venvs\solana-tracker\Scripts\python.exe -X utf8`. A bare `python.exe` is the 3.14 install, which has no websockets.

**Recorder:** `-m gemtracker.live --run recorder [--algos a,b,...]`
- Writes `data/paper/recorder/`: `config.json`, `status.json`, `summary.jsonl` and `<algo>.jsonl`.
- Clean stop: create `data/paper/recorder/STOP`.
- Set BelowNormal priority on the venv child process too.

**Dashboard:** `-m gemtracker.dashboard --port 8766`
- Serves http://127.0.0.1:8766.
- The HTML is re-read live. A Python change needs a restart: create `data/paper/recorder/DASHBOARD_STOP`.
- It reads the cards in `data/research/elite20/cards/*.json`.

**Tests:** `-m unittest discover -s tests -t tests`
- 224 OK at commit 291c8e1.
- pytest fails at collection on sibling imports, so don't use it.

**Latency.** Live latency is 2.5 s on pump and 5.5 s on pumpswap. Measured feed lag p50 is 3.6 s and 5.1 s.

## Code map
**`gemtracker/` core:**
- `live.py`: the recorder, `load_algos`, `--algos`.
- `market.py`: `TokenState`, the holder book, launch snipers.
- `chain_events.py`.
- `papersim.py`: fills, fees, latency.
- `strategy.py`.
- `rugcheck.py`: `check` and `risk_size_frac`.

**`gemtracker/` tools:**
- `dashboard.py` and `dashboard.html`.
- `scoreboard.py`.
- `histrun.py`: the live code path replayed over history.
- `bq.py`: BigQuery, with ADC through `scripts/gcloud.sh`; project solana-history-510919.
- `elite_*.py`.

**`gemtracker/algos/`:**
- Bases: `_scalp_a_base.py`, `_scalp_b_base.py` (ScalpBase, ET-day kill switch) and `swing_base_lib.py`.
- `baselines.py`: `base_random`, `base_hold60`, `base_elite_copy`.
- The old algo files, to be removed at the swap: cap, cented, cooker, cupsey, decu, elite5, frank_degods, mr_frog, smokez, theo, trenchman, trunoest.

**Data and research:**
- `data/history/` (git-ignored) holds HF jocry (Jun-Jul), HF Slinky21 (Aug-Sep), Kaggle memecoins (pump swaps 08-21..10-06, plus the first 60 s of PumpSwap after each migration) and cached elite trades.
- Kaggle downloads go through `bash scripts/kaggle.sh`, one file at a time with `-f`.
- `scripts/grad/` is the post-graduation engine. `data/research/elite20/` holds `BRIEF.md`, `cards/` and per-family folders.

## Research protocol (full text: `data/research/elite20/BRIEF.md`)
**Split.**
- FIT: ET days ≤ 2026-08-24.
- VAL: 08-25..09-04 (11 days).
- HOLDOUT: ≥ 09-05.

**Trial discipline.**
- Freeze a candidate before VAL, then run VAL once.
- A rerun counts as a new logged trial.
- Never tune on VAL.

**LIVE floor** (on VAL, at live latency, all fees in):
- net > 0;
- beats `base_random`;
- ≥ 20 round trips;
- green on ≥ 6 of 11 days;
- max drawdown ≤ 35%;
- alive at both 2.5 s and 5.5 s;
- worst day ≥ -15%;
- worst trade ≥ -6% of equity.

**TARGET gate:** geo ≥ +8.8%/day.

**Every buy:**
- passes `rugcheck.check`, which fails closed;
- is sized with `risk_size_frac` = `min(0.25, Kelly, 0.05/worst_loss)`;
- has a mandatory stop-loss;
- keeps open exposure ≤ 50%.

**Cards.** Write one card for every candidate, failures included. The VAL number on a card comes from `histrun` replaying the real algo class.

## Working together (the Claude-Codex bridge)
1. **Start of work.**
   - Read this file and `docs/HANDOFF.md`.
   - Then read your team inbox: the `team_board` MCP `read_inbox`, or the tail of `D:\Team\inbox\<you>.md`.
   - `D:\Team\BOARD.md` is about 240k characters. Grep it; never read it whole.
2. **One owner at a time.** The owner is named at the top of `docs/HANDOFF.md`. The other agent only reads, or posts a message (`post_message`, or a line in the owner's inbox) before touching anything.
3. **End of every work block.**
   - Rewrite the Now, Next and Open sections of `docs/HANDOFF.md`, with the ET time, and commit them together with the code.
   - Add one line with `log_work` (or append to `D:\Team\log\<YYYY-MM-DD>.md`).
4. **Handover.** Set the new owner in `docs/HANDOFF.md`, post a message to the other agent, and log it.
5. **Lessons.** A durable lesson goes in the Lessons section below, so both agents keep it. Never leave it only in one agent's private memory.

## Lessons (append; never delete without evidence)
- **Latency beats copying.** No elite-derived slice survives a 3 s delay once sniping is banned (age ≥ 30 s). 66-89% of elite trips are sub-30 s snipes, and the elites earn their own price impact (el_ 0/8 on FIT, 2026-10-07). Wave 1 of the pump-curve family (pc_) went 0/45 trials, negative even at 0 ms.
- **The old live algos.** They lost 15-24% in 90 minutes live, with 0 green ET-days.
- **BigQuery.** The free `Instructions` table keeps top-level instructions only, so it has no PumpSwap trade events. `Token Transfers` rebuilds swaps exactly, but costs about 22 GB per UTC day: there is no clustering, so the cost does not depend on the WHERE clause. Scan each day once and keep every derived table you need.
- **LaunchLab.** A TradeEvent has no user wallet, so rugcheck returns `partial_history` and the coin is unbuyable until the tx signer is attached.
- **RAM.** At 8:01 PM ET on 2026-10-07, parallel feature builds (about 11 GB) crashed the recorder and Rahul's bot. A `taskkill /IM python.exe` took down about 7 processes.
- **Dead or blocked sources.** The Dune free tier is dead, Old Faithful returns 429, and Google blocks the pydata OAuth client (use `scripts/gcloud.sh` ADC instead).
- **Slinky21 cache.** Some cache days are 0-byte files. Re-prep them; never silently skip them.
- **Targets.** Track them on the scoreboard. Never use them as a fitting objective.
