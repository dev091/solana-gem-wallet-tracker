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

Keys are read from environment variables (all optional, see .env.example):
  HELIUS_API_KEY / SOLANA_RPC_URL, SOLANATRACKER_API_KEY, GMGN_API_KEY, FOMOAPI_KEY,
  TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID, DISCORD_WEBHOOK_URL
"""


def _criteria_args(p: argparse.ArgumentParser) -> None:
    d = Criteria()
    g = p.add_argument_group("rules (defaults = $100-$500 in, $100k+ out, 4+ times, every trade 20x+)")
    g.add_argument("--entry-min", type=float, default=d.entry_min_usd, help="min USD entry per coin")
    g.add_argument("--entry-max", type=float, default=d.entry_max_usd, help="max USD entry per coin")
    g.add_argument("--gem-profit", type=float, default=d.gem_profit_usd, help="USD profit that makes a gem")
    g.add_argument("--min-gems", type=int, default=d.min_gems, help="gems needed (4 or 5)")
    g.add_argument("--min-multiple", type=float, default=d.min_multiple, help="every trade must reach this x")
    g.add_argument("--grace-hours", type=float, default=d.grace_hours,
                   help="trades younger than this are not judged yet")
    g.add_argument("--include-unrealized", action="store_true",
                   help="count coins still held (at today's price) toward gem profit")
    g.add_argument("--allow-other-entries", action="store_true",
                   help="do not require every trade to be a $100-$500 entry")
    g.add_argument("--max-tokens", type=int, default=d.max_tokens, help="more coins than this = bot")


def _criteria(a) -> Criteria:
    return Criteria(entry_min_usd=a.entry_min, entry_max_usd=a.entry_max, gem_profit_usd=a.gem_profit,
                    min_gems=a.min_gems, min_multiple=a.min_multiple, grace_hours=a.grace_hours,
                    count_unrealized=a.include_unrealized, all_entries_in_range=not a.allow_other_entries,
                    max_tokens=a.max_tokens)


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

    p = sub.add_parser("watch", help="alert on new buys by tracked wallets")
    p.add_argument("--loop", action="store_true", help="keep running (otherwise check once)")
    p.add_argument("--interval", type=float, default=30.0, help="seconds between checks with --loop")
    p.add_argument("--sells", action="store_true", help="also alert on sells")
    p.add_argument("--tiers", default="STRICT,GEM_HUNTER",
                   help="which scan results to track (STRICT, GEM_HUNTER)")
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
                            early_txs=a.early_txs, min_early_hits=a.min_early_hits, deadline=deadline)
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
    profit = "incl. holdings" if crit.count_unrealized else "cash taken out"
    parts = [f"entry {util.usd(crit.entry_min_usd)}-{util.usd(crit.entry_max_usd)}",
             f"profit ≥ {util.usd(crit.gem_profit_usd)} ({profit})",
             f"≥ {crit.min_gems} gems",
             f"every trade ≥ {crit.min_multiple:g}x"]
    if crit.all_entries_in_range:
        parts.append("no other kind of trade")
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
            note = "GEM" if is_gem(p, crit) else ("< {:g}x".format(crit.min_multiple)
                                                   if (p.multiple or 0) < crit.min_multiple else "")
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
        if a.command == "doctor":
            from .doctor import run as doctor
            return doctor()
        if a.command == "watch":
            from .watch import run
            tiers = tuple(t.strip().upper() for t in a.tiers.split(",") if t.strip())
            return run(loop=a.loop, interval=a.interval, include_sells=a.sells, tiers=tiers)
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
