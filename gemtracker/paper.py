"""Paper trading: would copying the tracked wallets have made money? No real money moves.

Every buy the watcher notices opens a paper position of STAKE_USD at the price *when we noticed*
(not the wallet's own fill: the delay is exactly what a copier suffers). Fees and slippage are
charged on both sides. Three exit rules are scored side by side on the same signals:

  mirror     sell when the copied wallet sells (or after MAX_HOLD_HOURS)
  tp2x_half  sell half at 2x if the price got there, the rest like `mirror`
  hold_24h   sell 24 hours after entry, whatever happens
"""
from __future__ import annotations

from . import config, util

STAKE_USD = 20.0
FEE_PCT = 2.0          # per side: DEX / Pump.fun fee + bot fee + priority fee + slippage
MAX_HOLD_HOURS = 48
LEDGER_FILE = config.DATA_DIR / "paper_ledger.json"
DASHBOARD_FILE = config.DOCS_DATA_DIR / "paper.json"
POLICIES = ("mirror", "tp2x_half", "hold_24h")


def net_multiple(entry: float, exit_price: float, fee_pct: float = FEE_PCT) -> float:
    """Money back per dollar staked after paying fees on the way in and out."""
    if not entry:
        return 0.0
    keep = 1 - fee_pct / 100
    return keep * keep * exit_price / entry


class PaperBook:
    def __init__(self, stake: float = STAKE_USD, fee_pct: float = FEE_PCT):
        data = util.load_json(LEDGER_FILE, {})
        self.open_positions: list = data.get("open") or []
        self.closed: list = data.get("closed") or []
        self.stake, self.fee_pct = stake, fee_pct

    # ------------------------------------------------------------- signals
    def on_buy(self, ev: dict, now: int) -> dict | None:
        """Open a paper position for a noticed buy (one open position per wallet+coin)."""
        price = ev.get("price")
        if not price or price <= 0:
            return None
        if any(p["wallet"] == ev["wallet"] and p["mint"] == ev["mint"] for p in self.open_positions):
            return None
        pos = {"wallet": ev["wallet"], "label": ev.get("label") or "", "tier": ev.get("tier") or "",
               "mint": ev["mint"], "symbol": ev.get("symbol") or util.short(ev["mint"]),
               "opened_at": now, "entry": price, "peak": price, "last": price,
               "price_24h": None, "wallet_buy_usd": ev.get("usd")}
        self.open_positions.append(pos)
        return pos

    def on_sell(self, wallet: str, mint: str, price: float | None, now: int) -> list:
        """The copied wallet sold: close our mirror of it."""
        closed = []
        for pos in [p for p in self.open_positions if p["wallet"] == wallet and p["mint"] == mint]:
            closed.append(self._close(pos, price if price is not None else pos["last"], now, "wallet sold"))
        return closed

    def mark(self, prices: dict, now: int) -> list:
        """Update open positions with fresh prices ({mint: price or 0 for dead}); close expired ones."""
        closed = []
        for pos in list(self.open_positions):
            if pos["mint"] in prices:
                price = prices[pos["mint"]] or 0.0
                pos["last"] = price
                pos["peak"] = max(pos["peak"], price)
            if pos["price_24h"] is None and now - pos["opened_at"] >= 24 * 3600:
                pos["price_24h"] = pos["last"]
            if now - pos["opened_at"] >= MAX_HOLD_HOURS * 3600:
                closed.append(self._close(pos, pos["last"], now, f"{MAX_HOLD_HOURS}h limit"))
        return closed

    def _close(self, pos: dict, price: float, now: int, reason: str) -> dict:
        self.open_positions.remove(pos)
        pos.update(closed_at=now, exit=price, reason=reason)
        if pos["price_24h"] is None:  # closed before 24h: the 24h rule would have exited at this price too
            pos["price_24h"] = price
        pos["returns"] = self.returns(pos)
        self.closed.append(pos)
        return pos

    # ------------------------------------------------------------- scoring
    def returns(self, pos: dict) -> dict:
        """Net multiple (1.0 = break-even) of each exit rule for one position."""
        entry, exit_price = pos["entry"], pos.get("exit", pos["last"])
        mirror = net_multiple(entry, exit_price, self.fee_pct)
        if pos["peak"] >= 2 * entry:
            tp = 0.5 * net_multiple(entry, 2 * entry, self.fee_pct) + 0.5 * mirror
        else:
            tp = mirror
        day = net_multiple(entry, pos["price_24h"] if pos["price_24h"] is not None else exit_price, self.fee_pct)
        return {"mirror": round(mirror, 4), "tp2x_half": round(tp, 4), "hold_24h": round(day, 4)}

    def summary(self) -> dict:
        def score(rows: list) -> dict:
            out = {"trades": len(rows)}
            for policy in POLICIES:
                mults = [r["returns"][policy] for r in rows]
                pnl = sum((m - 1) * self.stake for m in mults)
                out[policy] = {"pnl_usd": round(pnl, 2),
                               "win_rate": round(sum(m > 1 for m in mults) / len(mults), 3) if mults else None,
                               "avg_return_pct": round((sum(mults) / len(mults) - 1) * 100, 1) if mults else None,
                               "best_x": round(max(mults), 2) if mults else None}
            return out

        by_wallet = {}
        for row in self.closed:
            by_wallet.setdefault(row["wallet"], []).append(row)
        wallets = []
        for wallet, rows in by_wallet.items():
            item = score(rows)
            item.update(wallet=wallet, label=rows[-1].get("label") or "", tier=rows[-1].get("tier") or "")
            wallets.append(item)
        wallets.sort(key=lambda w: -w["mirror"]["pnl_usd"])
        return {"overall": score(self.closed), "wallets": wallets}

    def save(self, now: int) -> dict:
        util.save_json(LEDGER_FILE, {"open": self.open_positions, "closed": self.closed[-5000:]})
        payload = {"updated_at": now, "stake_usd": self.stake, "fee_pct_per_side": self.fee_pct,
                   "max_hold_hours": MAX_HOLD_HOURS, "summary": self.summary(),
                   "open": sorted(self.open_positions, key=lambda p: -p["opened_at"])[:200],
                   "closed": list(reversed(self.closed[-300:]))}
        util.save_json(DASHBOARD_FILE, payload, js_var="GEM_PAPER")
        return payload
