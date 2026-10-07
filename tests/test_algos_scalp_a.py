"""scalp_a reconstructions (Decu, Cented, Trunoest, Theo): synthetic launches through replay().

Checks: entry only when the filter holds, exits fire, no look-ahead (suffix invariance),
never exceeds cash / position caps, the liquidity cap holds, the daily kill switch stops
new entries, and the target elite's own wallet is never a signal.
"""
import unittest

from gemtracker import chain_events as ce
from gemtracker.algos._scalp_a_base import ScalpBase, impact_cap, price_after_buy
from gemtracker.algos.cented import Cented
from gemtracker.algos.decu import Decu
from gemtracker.algos.theo import Theo
from gemtracker.algos.trunoest import Trunoest
from gemtracker.market import Market
from gemtracker.papersim import PaperSim, SimConfig, buy_out
from gemtracker.replay import replay
from gemtracker.strategy import Buy
from gemtracker.tape import event_row

ALGOS = (Decu, Cented, Trunoest, Theo)
VSOL, VTOK = 40 * 10 ** 9, 800_000_000 * 10 ** 6   # 50 SOL mcap at launch
T0 = 1_000                                          # chain time of the create (s)
RX0 = T0 * 1000 + 5_000                             # first trade arrives at age 5 s


def trade(mint, user, side, sol, rq, rb, ts=0, venue="pump"):
    return ce.ChainEvent("trade", venue, f"s{user}{rq}", 0, ts=ts, mint=mint, user=user, side=side,
                         quote=int(sol * 1e9), tokens=10 ** 6, price=(rq / 1e9) / (rb / 1e6),
                         reserve_quote=rq, reserve_base=rb, fee_bps=100)


def create(mint, ts=T0):
    return ce.ChainEvent("create", "pump", "c" + mint, 0, ts=ts, mint=mint, user="dev" + mint,
                         extra={"creator": "dev" + mint, "name": mint, "symbol": mint})


def launch(mint="M", n=12, sol=0.5, rx0=RX0, step=300, rq0=VSOL, users=None):
    """create + n buys from distinct wallets with constant-product rising reserves."""
    rows = [(rx0 - 5_000 + 1, create(mint, ts=(rx0 - 5_000) // 1000))]
    rq = rq0
    k = rq0 * VTOK
    for i in range(n):
        rq += int(sol * 1e9)
        u = users[i] if users else f"b{i}{mint}"
        rows.append((rx0 + i * step, trade(mint, u, "buy", sol, rq, k // rq)))
    return rows, rq, k // rq


def run(rows_events, strat, latency=1000, start_usd=100.0, max_open=10):
    rows = [dict(event_row(ev, rx)) for rx, ev in sorted(rows_events, key=lambda r: r[0])]
    cfg = SimConfig(latency_ms=latency, venue_latency_ms={}, start_usd=start_usd,
                    max_open_positions=max_open)
    return replay([strat], cfg, rows, 100.0)


def fills(sim, name):
    return [f for f in getattr(sim.books[name], "_fills", [])]


class Recording:
    """Mixin: keep every fill and the cash after it."""
    def __init__(self):
        super().__init__()
        self.seen = []

    def on_fill(self, fill, book):
        self.seen.append((fill, book.cash_sol, len(book.positions)))
        super().on_fill(fill, book)


def rec(cls, **over):
    return type("R" + cls.__name__, (Recording, cls), over)()


class EntryTest(unittest.TestCase):
    def test_hot_launch_buys_quiet_launch_does_not(self):
        for cls in ALGOS:
            hot, rq, rb = launch("H", n=16)
            hot.append((RX0 + 60_000, trade("H", "late", "buy", 0.01, rq, rb)))
            s = rec(cls)
            run(hot, s)
            buys = [f for f, _, _ in s.seen if f.side == "buy" and f.status == "filled"]
            self.assertEqual(len(buys), 1, cls.__name__)
            self.assertIn(cls.target, buys[0].reason)
            quiet, rq, rb = launch("Q", n=3)
            quiet.append((RX0 + 60_000, trade("Q", "late", "buy", 0.01, rq, rb)))
            s = rec(cls)
            run(quiet, s)
            self.assertEqual([f for f, _, _ in s.seen if f.side == "buy"], [], cls.__name__)

    def test_dev_sell_blocks_entry(self):
        for cls in ALGOS:
            rows, rq, rb = launch("D", n=4)
            rows.append((RX0 + 4 * 300, trade("D", "devD", "sell", 0.1, rq, rb)))
            more, rq2, rb2 = launch("D", n=16, rx0=RX0 + 5 * 300, rq0=rq)
            rows += more[1:]
            s = rec(cls)
            run(rows, s)
            buys = [f for f, _, _ in s.seen if f.side == "buy"]
            if cls.dev_sold_blocks:
                self.assertEqual(buys, [], cls.__name__)
            else:   # Decu: the dev had already sold before 68 % of his measured entries
                self.assertEqual(len(buys), 1, cls.__name__)

    def test_min_entry_gap_throttles_entries(self):
        """Two hot launches 20 s apart: with a 100 s global gap only the first is bought,
        without it both are (the gap never blocks exits)."""
        rows, _, _ = launch("A", n=16)
        later, _, _ = launch("B", n=16, rx0=RX0 + 20_000)
        rows += later
        s = rec(Decu, min_entry_gap_s=100.0, max_positions=4)
        run(rows, s)
        self.assertEqual([f.mint for f, _, _ in s.seen if f.side == "buy"], ["A"])
        s = rec(Decu, min_entry_gap_s=0.0, max_positions=4)
        run(rows, s)
        self.assertEqual([f.mint for f, _, _ in s.seen if f.side == "buy"], ["A", "B"])

    def test_target_wallet_is_never_a_signal(self):
        for cls in ALGOS:
            s = cls()
            m = Market()
            rows, rq, rb = launch("T")
            for rx, ev in rows:
                st = m.apply(ev, rx)
            now = RX0 + 12 * 300
            book = PaperSim([s], SimConfig(venue_latency_ms={}), lambda: 100.0).books[s.name]
            own = trade("T", cls.target_wallet, "buy", 0.5, rq, rb)
            m.apply(own, now)
            self.assertEqual(s.on_trade(st, own, now, book), [], cls.__name__)
            other = trade("T", "someone", "buy", 0.5, rq, rb)
            m.apply(other, now + 1)
            out = s.on_trade(st, other, now + 1, book)
            self.assertEqual(len(out), 1, cls.__name__)
            self.assertIsInstance(out[0], Buy)

    def test_other_elites_exclude_target(self):
        s = Theo()
        st = Market()._token("X", 0)
        st.elite_buys = [(1, "Theo", 1.0), (2, "Cented", 1.0)]
        self.assertEqual(s.other_elites(st), {"Cented"})


class ExitTest(unittest.TestCase):
    def test_time_stop_sells_everything(self):
        for cls in ALGOS:
            rows, rq, rb = launch("E")
            end = RX0 + 12 * 300 + int(cls.time_stop_s * 1000) + 10_000
            for i in range(5):  # flat tape keeps the clock ticking
                rows.append((RX0 + 5_000 + i * 2_000, trade("E", f"f{i}", "buy", 0.001, rq, rb)))
            rows.append((end, trade("E", "late", "buy", 0.001, rq, rb)))
            s = rec(cls)
            sim, _ = run(rows, s)
            sells = [f for f, _, _ in s.seen if f.side == "sell"]
            self.assertTrue(sells and "time stop" in sells[-1].reason, cls.__name__)
            self.assertEqual(sim.books[s.name].positions, {}, cls.__name__)

    def test_take_profit_fires_on_pump(self):
        for cls in ALGOS:
            rows, rq, rb = launch("P", n=16)
            # two seconds after the fill the price jumps well past tp1
            k = rq * rb
            rq2 = int(rq * 1.5)
            rows.append((RX0 + 12 * 300 + 3_000, trade("P", "whale", "buy", 10, rq2, k // rq2)))
            rows.append((RX0 + 12 * 300 + 8_000, trade("P", "late", "buy", 0.001, rq2, k // rq2)))
            s = rec(cls)
            run(rows, s)
            sells = [f for f, _, _ in s.seen if f.side == "sell" and f.status == "filled"]
            self.assertTrue(sells and "take profit" in sells[0].reason, cls.__name__)
            self.assertGreater(sells[0].pnl_sol, 0, cls.__name__)

    def test_hard_stop_fires_on_dump(self):
        for cls in ALGOS:
            rows, rq, rb = launch("S", n=16)
            k = rq * rb
            rq2 = int(rq * 0.6)
            rows.append((RX0 + 12 * 300 + 3_000, trade("S", "whale", "sell", 10, rq2, k // rq2)))
            rows.append((RX0 + 12 * 300 + 8_000, trade("S", "late", "buy", 0.001, rq2, k // rq2)))
            s = rec(cls)
            run(rows, s)
            sells = [f for f, _, _ in s.seen if f.side == "sell" and f.status == "filled"]
            self.assertTrue(sells and "hard stop" in sells[0].reason, cls.__name__)


class RiskTest(unittest.TestCase):
    def test_never_exceeds_cash_or_position_caps(self):
        for cls in ALGOS:
            rows = []
            for j in range(8):  # eight hot launches at once, tiny book
                r, rq, rb = launch(f"C{j}", n=16, rx0=RX0 + j * 50)
                rows += r
                rows.append((RX0 + 30_000, trade(f"C{j}", "late", "buy", 0.001, rq, rb)))
            s = rec(cls, min_entry_gap_s=0.0)
            sim, _ = run(rows, s, start_usd=20.0)   # 0.2 SOL book
            self.assertTrue(s.seen, cls.__name__)
            for f, cash, n_open in s.seen:
                self.assertGreaterEqual(cash, 0.0, cls.__name__)
                self.assertLessEqual(n_open, cls.max_positions, cls.__name__)

    def test_size_is_a_fraction_of_equity(self):
        s = rec(Decu)
        rows, rq, rb = launch("F", n=16)
        rows.append((RX0 + 30_000, trade("F", "late", "buy", 0.001, rq, rb)))
        run(rows, s, start_usd=100.0)           # 1 SOL book at 100 $/SOL
        buy = [f for f, _, _ in s.seen if f.side == "buy"][0]
        self.assertAlmostEqual(buy.sol, Decu.size_frac * 1.0, places=3)

    def test_liquidity_cap_limits_impact(self):
        self.assertAlmostEqual(price_after_buy(impact_cap(VSOL, VTOK, 100, 0.05), 100, VSOL, VTOK)
                               / (VSOL / 1e9 / (VTOK / 1e6)), 1.05, places=4)
        s = rec(Trunoest)
        rq0 = 2 * 10 ** 9                        # thin pool: 2 SOL in reserves
        rows, rq, rb = launch("L", sol=0.05, rq0=rq0)
        rows.append((RX0 + 30_000, trade("L", "late", "buy", 0.001, rq, rb)))
        s.mcap_min_sol = 0                       # thin pool means tiny mcap
        run(rows, s, start_usd=10_000.0)         # 100 SOL book wants 12 SOL
        buy = [f for f, _, _ in s.seen if f.side == "buy"][0]
        self.assertLess(buy.sol, 0.1)
        pre = rq / 1e9 / (rb / 1e6)
        self.assertLessEqual(price_after_buy(buy.sol, 100, rq, rb) / pre, 1.05 + 1e-6)

    def test_daily_kill_switch_blocks_entries_until_next_day(self):
        s = rec(Decu, daily_kill_dd=0.03, min_entry_gap_s=0.0)
        rows, rq, rb = launch("K1", n=16)
        k = rq * rb
        rq2 = int(rq * 0.5)
        rows.append((RX0 + 12 * 300 + 3_000, trade("K1", "whale", "sell", 10, rq2, k // rq2)))
        rows.append((RX0 + 12 * 300 + 8_000, trade("K1", "late", "buy", 0.001, rq2, k // rq2)))
        r2, rq, rb = launch("K2", n=16, rx0=RX0 + 60_000)
        rows += r2
        rows.append((RX0 + 90_000, trade("K2", "late", "buy", 0.001, rq, rb)))
        day = 86_400_000
        r3, rq, rb = launch("K3", n=16, rx0=RX0 + day)
        rows += r3
        rows.append((RX0 + day + 30_000, trade("K3", "late", "buy", 0.001, rq, rb)))
        run(rows, s)
        buys = [f.mint for f, _, _ in s.seen if f.side == "buy" and f.status == "filled"]
        self.assertEqual(buys, ["K1", "K3"])


    def test_daily_kill_switch_keys_on_et_day_not_utc(self):
        """A kill at 23:00 UTC still blocks at 00:30 UTC (same ET day) and clears at 05:30 UTC
        (next ET day): the kill switch rolls with the scoreboard's US-Eastern day."""
        s = rec(Decu, daily_kill_dd=0.03, min_entry_gap_s=0.0)
        day = 86_400_000
        base = 10 * day - 3_600_000                      # 23:00 UTC = 7 pm ET
        rows, rq, rb = launch("K1", n=16, rx0=base)
        k = rq * rb
        rq2 = int(rq * 0.5)
        rows.append((base + 12 * 300 + 3_000, trade("K1", "whale", "sell", 10, rq2, k // rq2)))
        rows.append((base + 12 * 300 + 8_000, trade("K1", "late", "buy", 0.001, rq2, k // rq2)))
        r2, rq, rb = launch("K2", n=16, rx0=base + 5_400_000)       # 00:30 UTC, same ET day
        rows += r2
        rows.append((base + 5_400_000 + 30_000, trade("K2", "late", "buy", 0.001, rq, rb)))
        r3, rq, rb = launch("K3", n=16, rx0=base + 6 * 3_600_000 + 1_800_000)  # 05:30 UTC, next ET day
        rows += r3
        rows.append((base + 6 * 3_600_000 + 1_800_000 + 30_000, trade("K3", "late", "buy", 0.001, rq, rb)))
        run(rows, s)
        buys = [f.mint for f, _, _ in s.seen if f.side == "buy" and f.status == "filled"]
        self.assertEqual(buys, ["K1", "K3"])


class LookAheadTest(unittest.TestCase):
    def test_decisions_are_suffix_invariant(self):
        for cls in ALGOS:
            rows, rq, rb = launch("A")
            k = rq * rb
            rq2 = int(rq * 1.4)
            rows.append((RX0 + 12 * 300 + 4_000, trade("A", "whale", "buy", 5, rq2, k // rq2)))
            rows.append((RX0 + 12 * 300 + 9_000, trade("A", "late", "buy", 0.001, rq2, k // rq2)))
            full = cls()
            run(rows, full)
            for cut in range(4, len(rows)):
                part = cls()
                run(rows[:cut], part)
                self.assertEqual(list(part.decisions), list(full.decisions)[:len(part.decisions)], cls.__name__)


class LoaderTest(unittest.TestCase):
    def test_base_is_skipped_and_names_unique(self):
        from gemtracker.live import load_algos
        names = [s.name for s in load_algos("all")]
        self.assertEqual(len(names), len(set(names)))
        self.assertNotIn("base", names)
        for cls in ALGOS:
            self.assertIn(cls.name, names)
            self.assertTrue(issubclass(cls, ScalpBase))


if __name__ == "__main__":
    unittest.main()
