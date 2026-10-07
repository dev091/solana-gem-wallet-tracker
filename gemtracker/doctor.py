"""`python -m gemtracker doctor`: check every data source in a couple of minutes."""
from __future__ import annotations

import time

from . import config, net, sources, util
from .config import Criteria

BONK = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"


def _check(name: str, fn, log) -> object:
    started = time.monotonic()
    try:
        result = fn()
    except Exception as exc:
        log(f"✘ {name:<26} {time.monotonic() - started:5.1f}s  {type(exc).__name__}: {exc}")
        return None
    log(f"✔ {name:<26} {time.monotonic() - started:5.1f}s  {result}")
    return result


def run(log=print) -> int:
    from .pumpfun import early_buyers
    from .prices import SolPrice, token_quotes
    from .providers import make_provider
    from .solana import SolanaRpc, delta_from_rpc_tx

    rpc = SolanaRpc(config.rpc_url())
    sol = SolPrice()
    log(f"RPC: {net.redact(rpc.url)}")
    keys = [k for k in ("HELIUS_API_KEY", "SOLANA_RPC_URL", "SOLANATRACKER_API_KEY", "GMGN_API_KEY",
                        "FOMOAPI_KEY", "TELEGRAM_BOT_TOKEN", "DISCORD_WEBHOOK_URL") if config.env(k)]
    log(f"keys set: {', '.join(keys) or 'none'}\n")

    _check("solana getSlot", lambda: rpc.call("getSlot", []), log)

    def fomo_trade():
        infos, _ = rpc.signatures(config.FOMO_SIGNER, max_count=5)
        tx = rpc.transaction(infos[0]["signature"])
        signers = [k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"] if k.get("signer")]
        deltas = [delta_from_rpc_tx(tx, s) for s in signers if s != config.FOMO_SIGNER]
        return f"latest Fomo-signed tx {infos[0]['signature'][:12]}…, user deltas {[d.tokens for d in deltas if d]}"
    _check("fomo signer history", fomo_trade, log)

    _check("SOL price (hourly)", lambda: f"${sol.at(util.now() - 86400):.2f} a day ago, spot ${sol.spot():.2f}", log)
    def quotes():
        found = {m: (q.price, q.liquidity) for m, q in token_quotes([BONK]).items() if q.price}
        if not found:
            raise RuntimeError("no price from DexScreener or Jupiter")
        return f"BONK price/liquidity {found[BONK]}"
    _check("dexscreener + jupiter", quotes, log)
    _check("fomo top-50 snapshot", lambda: f"{len(sources.fomo_top50())} wallets", log)
    _check("kolscan leaderboard", lambda: sources.kolscan(10)[:3], log)
    coins = _check("pump.fun top coins", lambda: sources.pumpfun_top_coins(5), log)
    gecko = _check("geckoterminal pumpswap", lambda: sources.geckoterminal_pump_coins(5), log)

    coin_list = coins or gecko or []
    if coin_list:
        mint, symbol = coin_list[0]
        _check(f"early buyers {symbol or util.short(mint)}",
               lambda: early_buyers(rpc, mint, sol.at, Criteria(), early_txs=40)[1], log)

    wallet = next((w for w, label in sources.fomo_top50() if "#4 " in label), None)
    if wallet:
        def analyze():
            from .criteria import evaluate
            report = make_provider("rpc", max_txs=1500, log=lambda *_: None).report(wallet)
            v = evaluate(report, Criteria())
            return (f"{util.short(wallet)}: {v.tier}, {v.stats['trades']} trades, {v.stats['gems']} gems, "
                    f"{report.tx_count} txs; {(v.reasons or ['ok'])[0]}")
        _check("analyze Fomo #4 wallet", analyze, log)
    return 0
