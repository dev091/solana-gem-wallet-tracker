"""Command line: python -m gemtracker <discover|scan|run|analyze|watch> [options]"""
from __future__ import annotations

import argparse
import sys
import time

from . import config, util
from .config import Criteria

HELP = """\
Find Solana meme-coin wallets that keep turning $100-$500 into $100k+ and track them.

  python -m gemtracker run                 discover candidates + scan them (what the GitHub Action does)
  python -m gemtracker discover            only collect candidate wallets from leaderboards / gem search
  python -m gemtracker scan                judge the collected candidates against the rules
  python -m gemtracker analyze <WALLET>    full trade-by-trade check of one wallet
  python -m gemtracker watch [--loop]      alert when tracked wallets buy a coin
  python -m gemtracker doctor              check that every data source answers
  python -m gemtracker board               leaderboard snapshot: top-5 target, consistent winners
  python -m gemtracker paper               would copying the tracked wallets have made money?

Keys are read from environment variables (all optional, see .env.example):
  HELIUS_API_KEY / SOLANA_RPC_URL, SOLANATRACKER_API_KEY, GMGN_API_KEY, FOMOAPI_KEY,
  TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID, DISCORD_WEBHOOK_URL
"""


def _criteria_args(p: argparse.ArgumentParser) -> None:
    from .config import PRESETS
    g = p.add_argument_group("rules (default preset 'solana': every trade 5x+, zero losses, verified coins, "
                             "5+ trades; preset 'gems': $100-$500 -> $100k+ 4 times, every trade 20x+)")
    g.add_argument("--preset", default="solana", choices=sorted(PRESETS), help="starting set of rules")
    g.add_argument("--min-multiple", type=float, help="every trade must reach this x")
    g.add_argument("--min-trades", type=int, help="qualifying trades needed")
    g.add_argument("--min-gems", type=int, help="gems needed ($100-$500 in, $100k+ out); 0 = off")
    g.add_argument("--entry-min", type=float, help="min USD entry per coin")
    g.add_argument("--entry-max", type=float, help="max USD entry per coin")
    g.add_argument("--gem-profit", type=float, help="USD profit that makes a gem")
    g.add_argument("--grace-hours", type=float, help="trades younger than this are not judged yet")
    g.add_argument("--max-tokens", type=int, help="more coins than this = bot")
    g.add_argument("--include-unrealized", action="store_true", help="count holdings toward gem profit")
    g.add_argument("--allow-other-entries", action="store_true", help="do not require every entry in range")
    g.add_argument("--allow-unverified", action="store_true", help="do not require Jupiter-verified coins")


def _criteria(a) -> Criteria:
    overrides = {field: getattr(a, arg) for field, arg in (
        ("min_multiple", "min_multiple"), ("min_trades", "min_trades"), ("min_gems", "min_gems"),
        ("entry_min_usd", "entry_min"), ("entry_max_usd", "entry_max"), ("gem_profit_usd", "gem_profit"),
        ("grace_hours", "grace_hours"), ("max_tokens", "max_tokens")) if getattr(a, arg, None) is not None}
    if a.include_unrealized:
        overrides["count_unrealized"] = True
    if a.allow_other_entries:
        overrides["all_entries_in_range"] = False
    if a.allow_unverified:
        overrides["verified_only"] = False
    return Criteria.preset(a.preset, **overrides)


def _provider_args(p: argparse.ArgumentParser) -> None:
    g = p.add_argument_group("data")
    g.add_argument("--provider", default="auto", choices=["auto", "rpc", "solanatracker"],
                   help="auto = Solana Tracker if SOLANATRACKER_API_KEY is set, else on-chain RPC")
    g.add_argument("--max-txs", type=int, default=3000,
                   help="RPC: wallets with more transactions are skipped as bots")
    g.add_argument("--workers", type=int, default=6, help="RPC: parallel requests")


def _discover_args(p: argparse.ArgumentParser) -> None:
    from .sources import ALL_SOURCES
    g = p.add_argument_group("discovery")
    g.add_argument("--sources", default=",".join(ALL_SOURCES),
                   help=f"comma list from: {', '.join(ALL_SOURCES)}")
    g.add_argument("--top", type=int, default=10, help="top N wallets from each leaderboard")
    g.add_argument("--gem-coins", type=int, default=30,
                   help="how many of Pump.fun's biggest coins to search for gem hunters")
    g.add_argument("--max-age-days", type=float, default=365,
                   help="verified-early: coin launch window in days, 0 = any age (default 365)")
    g.add_argument("--early-txs", type=int, default=250,
                   help="pump-early: how many of each coin's first trades to read")
    g.add_argument("--min-early-hits", type=int, default=2,
                   help="pump-early: keep wallets that bought this many big coins early")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gemtracker", description=HELP,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("discover", help="collect candidate wallets")
    _discover_args(p)
    _criteria_args(p)

    for name, text in (("scan", "judge collected candidates"), ("run", "discover + scan")):
        p = sub.add_parser(name, help=text)
        _discover_args(p)
        _criteria_args(p)
        _provider_args(p)
        p.add_argument("--max-wallets", type=int, default=40, help="scan at most this many candidates")
        p.add_argument("--time-budget", type=float, default=0,
                       help="stop starting new wallets after this many minutes (0 = no limit)")
        if name == "scan":
            p.add_argument("--fresh", action="store_true", help="re-run discovery first")

    p = sub.add_parser("analyze", help="check one wallet trade by trade")
    p.add_argument("wallet")
    _criteria_args(p)
    _provider_args(p)

    sub.add_parser("doctor", help="check every data source (takes a minute or two)")

    sub.add_parser("paper", help="paper-trading results: would copying the tracked wallets have paid?")

    p = sub.add_parser("board", help="snapshot Pump.fun + Kolscan leaderboards: top-5 target, consistent winners")
    p.add_argument("--wallet", help="also show where this wallet stands (default: wallets/me.txt or MY_WALLET)")

    p = sub.add_parser("watch", help="alert on new buys by tracked wallets")
    p.add_argument("--loop", action="store_true", help="keep running (otherwise check once)")
    p.add_argument("--interval", type=float, default=30.0, help="seconds between checks with --loop")
    p.add_argument("--sells", action="store_true", help="also alert on sells")
    p.add_argument("--tiers", default="STRICT,GEM_HUNTER",
                   help="which scan results to track (STRICT, GEM_HUNTER)")
    p.add_argument("--board", type=int, default=15,
                   help="also track this many of the most consistent leaderboard wallets (0 = none)")
    p.add_argument("--mode", default="holdings", choices=["holdings", "txs"],
                   help="holdings: cheap, works on the free RPC; txs: exact, needs a fast RPC")
    return parser


def _sources(a) -> list:
    return [s.strip() for s in a.sources.split(",") if s.strip()]


_STARTED = time.monotonic()
DISCOVERY_SHARE = 0.4  # with --time-budget, discovery may use up to 40% of it, scanning the rest


def _minutes_left(a) -> float:
    budget = getattr(a, "time_budget", 0) or 0
    return budget - (time.monotonic() - _STARTED) / 60 if budget else 0


def cmd_discover(a, log=print):
    from .sources import discover
    budget = getattr(a, "time_budget", 0) or 0
    deadline = _STARTED + budget * 60 * DISCOVERY_SHARE if budget else None
    book, status = discover(_sources(a), a.top, a.gem_coins, _criteria(a), log,
                            early_txs=a.early_txs, min_early_hits=a.min_early_hits, deadline=deadline,
                            max_age_days=a.max_age_days or None)
    util.save_json(config.DATA_DIR / "candidates.json",
                   {"generated_at": util.now(), "sources": status, "candidates": book.to_list()})
    log(f"\n{len(book.by_wallet)} candidate wallet(s) saved to data/candidates.json")
    return book, status


def cmd_scan(a, fresh: bool, log=print) -> int:
    from .providers import make_provider
    from .scan import save_results, scan
    from .sources import CandidateBook
    crit = _criteria(a)
    saved = util.load_json(config.DATA_DIR / "candidates.json", {})
    if fresh or not saved.get("candidates"):
        book, status = cmd_discover(a, log)
    else:
        book, status = CandidateBook.from_list(saved["candidates"]), saved.get("sources") or {}
        log(f"Using {len(book.by_wallet)} candidate(s) from data/candidates.json (--fresh to re-discover)")
    candidates = book.ordered()
    if not candidates:
        log("No candidates. Add wallets to wallets/seeds.txt or set an API key (see README).")
        save_results([], crit, "-", status)
        return 1
    provider = make_provider(a.provider, max_txs=a.max_txs, workers=a.workers, max_tokens=crit.max_tokens,
                             log=log)
    log(f"\nScanning up to {a.max_wallets} wallet(s) with {provider.describe()}")
    log(_rules_line(crit) + "\n")
    minutes = max(_minutes_left(a), 1.0) if a.time_budget else 0
    results = scan(candidates, provider, crit, a.max_wallets, log, time_budget_min=minutes)
    payload = save_results(results, crit, provider.name, status)
    c = payload["counts"]
    log(f"\nDone: {c['scanned']} scanned · {c['strict']} STRICT · {c['gem_hunter']} GEM_HUNTER · "
        f"{c['rejected']} rejected · {c['error']} errors")
    log("Results: docs/data/wallets.json (open docs/index.html) · tracked list: data/tracked.json")
    return 0


def _rules_line(crit: Criteria) -> str:
    parts = [f"every trade ≥ {crit.min_multiple:g}x (zero losses)"]
    if crit.min_gems:
        profit = "incl. holdings" if crit.count_unrealized else "cash taken out"
        parts.append(f"≥ {crit.min_gems} gems of {util.usd(crit.entry_min_usd)}-{util.usd(crit.entry_max_usd)} in, "
                     f"+{util.usd(crit.gem_profit_usd)} out ({profit})")
    else:
        parts.append(f"≥ {crit.min_trades} such trades")
    if crit.verified_only:
        parts.append("verified coins only")
    if crit.all_entries_in_range:
        parts.append(f"every entry {util.usd(crit.entry_min_usd)}-{util.usd(crit.entry_max_usd)}")
    return "Rules: " + ", ".join(parts)


def cmd_analyze(a, log=print) -> int:
    from .criteria import evaluate, is_gem
    from .providers import make_provider
    if not util.is_address(a.wallet):
        log(f"{a.wallet!r} is not a Solana address")
        return 2
    crit = _criteria(a)
    provider = make_provider(a.provider, max_txs=a.max_txs, workers=a.workers, max_tokens=crit.max_tokens,
                             log=log)
    log(f"Analyzing {a.wallet} with {provider.describe()}…")
    report = provider.report(a.wallet)
    verdict = evaluate(report, crit)
    trades = sorted(verdict.trades, key=lambda p: p.first_buy_ts or 0)
    if trades:
        log(f"\n{'date':<10}  {'coin':<12} {'in':>9} {'out':>9} {'held':>9} {'x':>8}  note")
        for p in trades:
            note = ("GEM" if crit.min_gems and is_gem(p, crit) else
                    "< {:g}x".format(crit.min_multiple) if (p.multiple or 0) < crit.min_multiple else "ok")
            if crit.verified_only and p.verified is False:
                note += " (unverified)"
            log(f"{util.date(p.first_buy_ts):<10}  {(p.symbol or util.short(p.mint))[:12]:<12} "
                f"{util.usd(p.cost_usd):>9} {util.usd(p.proceeds_usd):>9} {util.usd(p.value_usd):>9} "
                f"{util.mult(p.multiple):>8}  {note}")
    log("\n" + _rules_line(crit))
    log(f"Verdict: {verdict.tier}")
    for reason in verdict.reasons:
        log(f"  ✘ {reason}")
    for flag in verdict.flags:
        log(f"  ⚠ {flag}")
    for note in report.notes:
        log(f"  • {note}")
    s = verdict.stats
    log(f"  {s['gems']} gem(s) · {s['trades']} trade(s) · worst {util.mult(s['min_multiple'])} · "
        f"median {util.mult(s['median_multiple'])} · realized {util.usd(s['realized_usd'])}")
    return 0


def my_wallet(explicit: str | None = None) -> str | None:
    for candidate in (explicit, config.env("MY_WALLET"),
                      *[w for w, _ in util.read_wallet_list(config.MY_WALLET_FILE)][:1]):
        if candidate and util.is_address(candidate):
            return candidate
    return None


def cmd_paper(log=print) -> int:
    from .paper import POLICIES, PaperBook
    book = PaperBook()
    summary = book.summary()
    o = summary["overall"]
    log(f"Paper trading: ${book.stake:g} per signal, {book.fee_pct:g}% fees+slippage each side; "
        f"{len(book.open_positions)} open, {o['trades']} closed")
    if not o["trades"]:
        log("No closed paper trades yet; `watch` opens them as tracked wallets buy.")
        return 0
    for policy in POLICIES:
        r = o[policy]
        log(f"  {policy:<10} PnL {util.usd(r['pnl_usd']):>8}  win rate {r['win_rate']:.0%}  "
            f"avg {r['avg_return_pct']:+.1f}%  best {r['best_x']}x")
    log("\nBy wallet (exit when the wallet sells):")
    for w in summary["wallets"][:20]:
        m = w["mirror"]
        log(f"  {w['label'][:28] or util.short(w['wallet']):<28} {w['trades']:>3} trades  "
            f"PnL {util.usd(m['pnl_usd']):>8}  win {m['win_rate']:.0%}  avg {m['avg_return_pct']:+.1f}%")
    return 0


def cmd_board(a, log=print) -> int:
    from . import leaderboard as lb
    snap = lb.take_snapshot(log)
    if not snap["boards"]:
        return 1
    history, seen = lb.record(snap)
    payload = lb.save_dashboard(snap, history, seen)
    log("\nProfit needed per rank (USD):")
    for name, steps in payload["ladders"].items():
        log(f"  {name:<17} " + "  ".join(f"#{rank} {util.usd(v)}" for rank, v in steps.items()))
    daily = snap["boards"].get("pump.fun daily") or []
    if daily:
        log("\nPump.fun top 5, last 24h:")
        for r in daily[:5]:
            coins = f" on {r.positions} coins" if r.positions else ""
            log(f"  #{r.rank} {r.name or util.short(r.wallet):<18} {util.usd(r.pnl_usd):>9}  "
                f"bought {r.spent_sol or 0:,.0f} SOL{coins}")
    log("\nMost consistent wallets (several boards / days):")
    for r in payload["repeat_leaders"][:10]:
        log(f"  {r['name'] or util.short(r['wallet']):<18} score {r['score']:>2}  best #{r['best_rank']:<3} "
            f"on: {', '.join(r['boards_now']) or '-'}")
    log("\nBig returns on small money (<= 25 SOL bought in the window, Pump.fun ROI >= 300%):")
    for r in payload["efficient_winners"][:10]:
        log(f"  {r['name'] or util.short(r['wallet']):<18} {r['board']:<16} #{r['rank']:<3} "
            f"{util.usd(r['pnl_usd']):>9}, bought {r['spent_sol']:.1f} SOL, ROI {r['roi_pct']:,.0f}%")
    wallet = my_wallet(getattr(a, "wallet", None))
    if wallet:
        log(f"\nYour wallet {util.short(wallet)}:")
        for name, rank, pnl, cutoff5, cutoff_last in lb.wallet_standing(snap, wallet):
            where = f"#{rank} ({util.usd(pnl)})" if rank else f"not in the list (last place {util.usd(cutoff_last)})"
            log(f"  {name:<17} {where}; top 5 needs {util.usd(cutoff5)}")
    log("\nSaved: data/leaderboards/ and docs/data/leaderboard.json")
    return 0


def main(argv=None) -> int:
    config.load_dotenv()
    parser = build_parser()
    a = parser.parse_args(argv)
    if not a.command:
        parser.print_help()
        return 0
    try:
        if a.command == "discover":
            cmd_discover(a)
            return 0
        if a.command == "scan":
            return cmd_scan(a, fresh=a.fresh)
        if a.command == "run":
            return cmd_scan(a, fresh=True)
        if a.command == "analyze":
            return cmd_analyze(a)
        if a.command == "board":
            return cmd_board(a)
        if a.command == "paper":
            return cmd_paper()
        if a.command == "doctor":
            from .doctor import run as doctor
            return doctor()
        if a.command == "watch":
            from .watch import run
            tiers = tuple(t.strip().upper() for t in a.tiers.split(",") if t.strip())
            return run(loop=a.loop, interval=a.interval, include_sells=a.sells, tiers=tiers,
                       board=a.board, mode=a.mode)
    except KeyboardInterrupt:
        print("\nstopped")
        return 130
    except Exception as exc:  # show a clean message, not a traceback, for expected failures
        from .net import HttpError
        from .providers import ProviderError
        from .solana import RpcError
        if isinstance(exc, (HttpError, ProviderError, RpcError)):
            print(f"error: {exc}", file=sys.stderr)
            return 1
        raise
    return 0
