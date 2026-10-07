"""swing_base group: Mr. Frog, Smokez, Frank degods reconstructions and the shared baselines.

Synthetic ChainEvents go through replay() exactly as the live runner would feed them, so each
test checks the whole path: market state -> strategy decision -> latency -> fill. Paper only.
"""
import unittest
from types import SimpleNamespace

from gemtracker import chain_events as ce
from gemtracker.algos.baselines import BaseEliteCopy, BaseHold60, BaseRandom
from gemtracker.algos.frank_degods import FrankDegods
from gemtracker.algos.mr_frog import MrFrog
from gemtracker.algos.smokez import Smokez
from gemtracker.algos.swing_base_lib import Tracked, unit_hash
from gemtracker.papersim import SimConfig, buy_out
from gemtracker.replay import replay
from gemtracker.strategy import Strategy
from gemtracker.tape import event_row

VSOL, VTOK = 40 * 10 ** 9, 800_000_000 * 10 ** 6       # launch-ish curve: mcap 50 SOL
MRFROG = "4DdrfiDHpmx55i4SPssxVzS9ZaKLb8qr45NKY9Er9nNh"
SMOKEZ = "5t9xBNuDdGTGpjaPTx6hKd7sdRJbvtKS8Mhq6qVbo8Qz"
FRANK = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
TARGETS = {MRFROG: "Mr. Frog", SMOKEZ: "Smokez", FRANK: "Frank degods"}


def create(rx, mint="M", dev="dev", venue="pump", rq=VSOL, rb=VTOK, mayhem=False):
    ev = ce.ChainEvent("create", venue, f"c{rx}", 0, mint=mint, user=dev,
                       price=(rq / 1e9) / (rb / 1e6), reserve_quote=rq, reserve_base=rb,
                       extra={"creator": dev, "mayhem": mayhem})
    return rx, ev


def trade(rx, user, side="buy", sol=1.0, rq=VSOL, rb=VTOK, mint="M", venue="pump", tokens=1.0):
    ev = ce.ChainEvent("trade", venue, f"t{rx}{user}", 0, mint=mint, user=user, side=side,
                       quote=int(sol * 1e9), tokens=int(tokens * 1e6), price=(rq / 1e9) / (rb / 1e6),
                       reserve_quote=rq, reserve_base=rb, fee_bps=100)
    return rx, ev


def run(rows_events, strat, latency=1000, elite_names=None):
    """Replay synthetic rows through one strategy; the book gets a `fill_log` of every Fill seen."""
    log, inner = [], strat.on_fill

    def on_fill(fill, book):
        log.append(fill)
        inner(fill, book)
    strat.on_fill = on_fill
    rows = [dict(event_row(ev, rx)) for rx, ev in rows_events]
    sim, market = replay([strat], SimConfig(latency_ms=latency, venue_latency_ms={}), rows, 100.0,
                         elite_names=elite_names)
    book = sim.books[strat.name]
    book.fill_log = log
    return book, market


def fills(book, side=None, status="filled"):
    return [f for f in book.fill_log if (side is None or f.side == side) and f.status == status]


def decisions(book):
    """What the strategy decided, independent of how later rows filled it."""
    return [(f.side, f.mint, f.decision_ms, round(f.decision_price, 12), round(f.sol, 9), f.reason)
            for f in book.fill_log]


# ---------------------------------------------------------------- scenarios
def frog_launch(buyers=("a", "b", "c"), t0=1000, mayhem=False, dev_sells=False, step=1000):
    rows = [create(t0, mayhem=mayhem)]
    t = t0
    if dev_sells:
        rows += [trade(t0 + 200, "dev"), trade(t0 + 400, "dev", "sell", 0.5)]
    for u in buyers:
        t += step
        rows.append(trade(t, u))
    return rows, t


def smokez_run(users=("a", "b", "c", "d"), rqs=(100e9, 110e9, 120e9, 125e9), t0=1000, start=22_000):
    rows = [create(t0, rq=int(100e9))]
    t = t0 + start
    for u, rq in zip(users, rqs):
        rows.append(trade(t, u, rq=int(rq)))
        t += 2000
    return rows, t - 2000


def frank_run(n=61, rq0=3000e9, rq1=3150e9, t0=1000, step=1000):
    rows = []
    for i in range(n):
        rq = rq0 + (rq1 - rq0) * i / (n - 1)
        rows.append(trade(t0 + i * step, f"u{i}", rq=int(rq), venue="pumpswap"))
    return rows, t0 + (n - 1) * step


class MrFrogTest(unittest.TestCase):
    def test_enters_on_launch_flow_and_takes_profit(self):
        rows, t = frog_launch()
        rows += [trade(t + 2000, "d"), trade(t + 3000, "e", rq=int(1.5 * VSOL)), trade(t + 5000, "f", rq=int(1.5 * VSOL))]
        book, _ = run(rows, MrFrog())
        buys, sells = fills(book, "buy"), fills(book, "sell")
        self.assertEqual(len(buys), 1)
        self.assertEqual(buys[0].decision_ms, t)                 # decided at the third buyer
        self.assertEqual(buys[0].arrival_ms, t + 1000)
        self.assertEqual(len(sells), 1)
        self.assertTrue(sells[0].reason.startswith("take-profit"), sells[0].reason)
        self.assertGreater(sells[0].pnl_sol, 0)
        self.assertNotIn("M", book.positions)

    def test_stop_loss_closes_position(self):
        rows, t = frog_launch()
        rows += [trade(t + 2000, "d"), trade(t + 3000, "e", "sell", rq=int(0.7 * VSOL)), trade(t + 5000, "f", rq=int(0.7 * VSOL))]
        book, _ = run(rows, MrFrog())
        sells = fills(book, "sell")
        self.assertEqual(len(sells), 1)
        self.assertTrue(sells[0].reason.startswith("stop"), sells[0].reason)
        self.assertLess(sells[0].pnl_sol, 0)

    def test_time_stop_fires_from_ticks(self):
        rows, t = frog_launch()
        rows += [trade(t + 2000 + 5000 * k, "d") for k in range(0, 27)]   # flow never fades
        book, _ = run(rows, MrFrog())
        sells = fills(book, "sell")
        self.assertEqual(len(sells), 1)
        self.assertTrue(sells[0].reason.startswith("time stop"), sells[0].reason)
        held = sells[0].decision_ms - fills(book, "buy")[0].arrival_ms
        self.assertGreaterEqual(held, 120_000)
        self.assertLess(held, 122_000)

    def test_sells_when_the_follower_wave_is_over(self):
        rows, t = frog_launch()
        rows += [trade(t + 2000, "d"), trade(t + 13_000, "g", "sell", sol=0.1)]
        book, _ = run(rows, MrFrog())
        sells = fills(book, "sell")
        self.assertEqual(len(sells), 1)
        self.assertTrue(sells[0].reason.startswith("wave over"), sells[0].reason)
        self.assertEqual(sells[0].decision_ms, t + 13_000)   # first second with no 10 s inflow after 6 s held

    def test_no_entry_when_filter_fails(self):
        cases = {
            "too few buyers": frog_launch(buyers=("a", "b"))[0],
            "too old": frog_launch(step=12_000)[0],
            "dev sold": frog_launch(dev_sells=True)[0],
            "mayhem": frog_launch(mayhem=True)[0],
            "no create seen": frog_launch()[0][1:],
            "one big elite buy": [create(1000), trade(2000, MRFROG, sol=5.0)],
        }
        for label, rows in cases.items():
            book, _ = run(rows, MrFrog(), elite_names=TARGETS)
            self.assertEqual(book.fill_log, [], label)

    def test_one_attempt_per_coin(self):
        rows, t = frog_launch()
        rows += [trade(t + 1000, "d", "sell", rq=int(0.7 * VSOL)), trade(t + 3000, "e", rq=int(0.7 * VSOL)),
                 trade(t + 4000, "f"), trade(t + 5000, "g"), trade(t + 6000, "h")]
        book, _ = run(rows, MrFrog())
        self.assertEqual(len(fills(book, "buy")), 1)


class SmokezTest(unittest.TestCase):
    def test_enters_on_mid_curve_momentum(self):
        rows, t = smokez_run()
        rows.append(trade(t + 2000, "e", rq=int(125e9)))
        book, market = run(rows, Smokez())
        buys = fills(book, "buy")
        self.assertEqual(len(buys), 1)
        self.assertEqual(buys[0].decision_ms, t)
        self.assertGreaterEqual(market.get("M").mcap, Smokez.min_entry_mcap_sol)

    def test_partial_take_profit_then_trailing_exit(self):
        rows, t = smokez_run()
        rows += [trade(t + 2000, "e", rq=int(125e9)), trade(t + 4000, "f", rq=int(190e9)),
                 trade(t + 6000, "g", rq=int(190e9)), trade(t + 8000, "h", "sell", rq=int(140e9)),
                 trade(t + 10_000, "i", rq=int(140e9))]
        book, _ = run(rows, Smokez())
        sells = fills(book, "sell")
        self.assertEqual([s.reason.split()[0] for s in sells], ["take-profit", "trail"])
        self.assertNotIn("M", book.positions)
        self.assertGreater(sum(s.pnl_sol for s in sells), 0)

    def test_tight_stop(self):
        rows, t = smokez_run()
        rows += [trade(t + 2000, "e", rq=int(125e9)), trade(t + 4000, "f", "sell", rq=int(100e9)),
                 trade(t + 6000, "g", rq=int(100e9))]
        book, _ = run(rows, Smokez())
        self.assertTrue(fills(book, "sell")[0].reason.startswith("stop"))

    def test_no_entry_when_filter_fails(self):
        flat, _ = smokez_run(rqs=(100e9, 102e9, 104e9, 105e9))          # +5 % only
        young, _ = smokez_run(start=5000)                                # inside the launch scramble
        few, _ = smokez_run(users=("a", "b", "c"), rqs=(100e9, 110e9, 125e9))
        launch, _ = smokez_run(rqs=(40e9, 44e9, 48e9, 50e9))             # mcap below the band
        elite_only, _ = smokez_run(users=(SMOKEZ, SMOKEZ, SMOKEZ, SMOKEZ))
        for label, rows in {"flat": flat, "young": young, "few buyers": few, "launch mcap": launch,
                            "elite only": elite_only}.items():
            book, _ = run(rows, Smokez(), elite_names=TARGETS)
            self.assertEqual(book.fill_log, [], label)


class FrankDegodsTest(unittest.TestCase):
    def test_enters_migrated_coin_on_sustained_flow(self):
        rows, t = frank_run()
        rows.append(trade(t + 2000, "z", rq=int(3150e9), venue="pumpswap"))
        book, market = run(rows, FrankDegods())
        buys = fills(book, "buy")
        self.assertEqual(len(buys), 1)
        self.assertEqual(buys[0].venue, "pumpswap")
        self.assertTrue(market.get("M").migrated)
        self.assertGreaterEqual(buys[0].sol, 0.15)          # concentrated: 20 % of 1 SOL equity

    def test_flow_breakdown_exit_under_water(self):
        rows, t = frank_run()
        rows.append(trade(t + 2000, "z", rq=int(3150e9), venue="pumpswap"))
        t2 = t + 2000 + 65_000                                # a quiet minute, then heavy selling
        rows += [trade(t2 + i * 500, f"s{i}", "sell", sol=2.0, rq=int(3100e9), venue="pumpswap") for i in range(6)]
        rows.append(trade(t2 + 4000, "y", rq=int(3100e9), venue="pumpswap"))
        book, _ = run(rows, FrankDegods())
        sells = fills(book, "sell")
        self.assertEqual(len(sells), 1)
        self.assertEqual(sells[0].reason, "flow breakdown")

    def test_partial_take_profit_at_double(self):
        rows, t = frank_run()
        rows += [trade(t + 2000, "z", rq=int(3150e9), venue="pumpswap"),
                 trade(t + 4000, "y", rq=int(6500e9), venue="pumpswap"),
                 trade(t + 6000, "x", rq=int(6500e9), venue="pumpswap")]
        book, _ = run(rows, FrankDegods())
        sells = fills(book, "sell")
        self.assertEqual(len(sells), 1)
        self.assertTrue(sells[0].reason.startswith("take-profit"))
        self.assertIn("M", book.positions)                   # half is still held

    def test_no_entry_when_filter_fails(self):
        oversized, _ = frank_run(rq0=20_000e9, rq1=21_000e9)  # above the sanity band (mis-scaled pools)
        thin, _ = frank_run(n=20)                             # not enough history / holders
        curve, _ = frank_run()                                # same flow but still on the curve
        curve = [(rx, ce.ChainEvent(**{**vars(ev), "venue": "pump"})) for rx, ev in curve]
        falling, _ = frank_run(rq0=3150e9, rq1=3000e9)
        for label, rows in {"oversized": oversized, "thin": thin, "curve": curve, "falling": falling}.items():
            book, _ = run(rows, FrankDegods())
            self.assertEqual(book.fill_log, [], label)


class NoPeekingTest(unittest.TestCase):
    """Decisions up to T must not depend on rows after T, and never on the target's wallet."""

    def scenarios(self):
        frog, t = frog_launch()
        frog_a = frog + [trade(t + 2000, "d"), trade(t + 3000, "e", rq=int(1.5 * VSOL)), trade(t + 5000, "f")]
        frog_b = frog + [trade(t + 2000, "d"), trade(t + 3000, "e", "sell", rq=int(0.6 * VSOL)), trade(t + 5000, "f")]
        smk, t = smokez_run()
        smk_a = smk + [trade(t + 2000, "e", rq=int(125e9)), trade(t + 4000, "f", rq=int(190e9))]
        smk_b = smk + [trade(t + 2000, "e", rq=int(125e9)), trade(t + 4000, "f", "sell", rq=int(90e9))]
        frk, t = frank_run()
        frk_a = frk + [trade(t + 2000, "z", rq=int(3150e9), venue="pumpswap"), trade(t + 4000, "y", rq=int(6500e9), venue="pumpswap")]
        frk_b = frk + [trade(t + 2000, "z", rq=int(3150e9), venue="pumpswap"), trade(t + 4000, "y", "sell", rq=int(2000e9), venue="pumpswap")]
        return [(MrFrog, frog_a, frog_b, t), (Smokez, smk_a, smk_b, t), (FrankDegods, frk_a, frk_b, t)]

    def test_suffix_invariance(self):
        for cls, a, b, _ in self.scenarios():
            cut = next(rx for (rx, x), (_, y) in zip(a, b) if vars(x) != vars(y))   # first differing row
            da = [d for d in decisions(run(a, cls())[0]) if d[2] < cut]
            db = [d for d in decisions(run(b, cls())[0]) if d[2] < cut]
            self.assertTrue(da, cls.name)
            self.assertEqual(da, db, cls.name)

    def test_target_wallet_is_not_a_signal(self):
        """Swapping the target's wallet for an unknown one changes nothing (its trades are tape, not signal)."""
        for cls, a, _, _ in self.scenarios():
            wallet = {MrFrog: MRFROG, Smokez: SMOKEZ, FrankDegods: FRANK}[cls]
            swapped = [(rx, ce.ChainEvent(**{**vars(ev), "user": wallet if ev.user in ("b", "u5", "e") else ev.user}))
                       for rx, ev in a]
            plain = decisions(run(a, cls(), elite_names=TARGETS)[0])
            with_target = decisions(run(swapped, cls(), elite_names=TARGETS)[0])
            self.assertTrue(plain, cls.name)
            self.assertEqual(plain, with_target, cls.name)

    def test_cash_never_negative_even_when_oversized(self):
        class Greedy(BaseHold60):
            name = "greedy"
            size_frac = 3.0        # asks for more than the whole stake every time
        rows = []
        for i in range(12):
            m = f"C{i}"
            rows += [create(1000 + i * 100, mint=m), trade(7000 + i * 100, "a", mint=m), trade(8000 + i * 100, "b", mint=m)]
        rows += [trade(80_000 + i * 100, "c", mint=f"C{i}") for i in range(12)]
        book, _ = run(rows, Greedy())
        self.assertTrue(fills(book, "buy"))
        self.assertGreaterEqual(book.cash_sol, 0.0)
        spent = sum(f.sol + f.tx_fee_sol for f in fills(book, "buy"))
        self.assertLessEqual(spent, book.start_sol + 1e-9)


class RiskAndSizingTest(unittest.TestCase):
    def fake_book(self, cash, start=1.0):
        b = SimpleNamespace(cash_sol=cash, start_sol=start, positions={}, pending=[])
        b.pending_buy_sol = lambda: 0.0
        b.equity_sol = lambda m: b.cash_sol
        return b

    def test_size_is_a_fraction_of_current_equity(self):
        s = Smokez()
        self.assertAlmostEqual(s.size_sol(self.fake_book(1.0)), 0.08)
        self.assertAlmostEqual(s.size_sol(self.fake_book(2.5)), 0.20)   # compounding
        b = BaseRandom()
        self.assertAlmostEqual(b.size_sol(self.fake_book(2.5)), 0.05)   # baselines: fixed on the start stake

    def test_liquidity_cap_limits_price_impact(self):
        st = SimpleNamespace(reserve_quote=VSOL, reserve_base=VTOK, fee_bps=100)
        t = Tracked()
        cap = t.liquidity_cap_sol(st, 10.0)
        self.assertLess(cap, 10.0)
        tokens, fee = buy_out(cap, 100, VSOL, VTOK)
        post = (VSOL + (cap - fee) * 1e9) / (VTOK - tokens * 1e6)
        self.assertLessEqual(post / (VSOL / VTOK) - 1, 0.05 + 1e-6)
        self.assertGreater(post / (VSOL / VTOK) - 1, 0.045)
        self.assertEqual(t.liquidity_cap_sol(st, 0.01), 0.01)

    def test_daily_kill_switch_and_caps(self):
        class R(Tracked):
            daily_kill_dd, max_positions, max_exposure_frac = 0.10, 2, 0.5
        r, day = R(), 86_400_000
        b = self.fake_book(1.0)
        self.assertTrue(r.may_enter(b, day + 1000))
        b.cash_sol = 0.95
        self.assertTrue(r.may_enter(b, day + 2000))
        b.cash_sol = 0.89
        self.assertFalse(r.may_enter(b, day + 3000))          # -11 % on the day: halted
        b.cash_sol = 1.2
        self.assertFalse(r.may_enter(b, day + 4000))          # stays halted for the UTC day
        self.assertTrue(r.may_enter(b, 2 * day + 1000))       # new day, new start-of-day equity
        b.positions = {"a": SimpleNamespace(cost_sol=0.1), "b": SimpleNamespace(cost_sol=0.1)}
        self.assertFalse(r.may_enter(b, 2 * day + 2000))      # position cap
        b.positions = {"a": SimpleNamespace(cost_sol=0.7)}
        self.assertFalse(r.may_enter(b, 2 * day + 3000))      # exposure cap


class BaselineTest(unittest.TestCase):
    def new_coins(self, n=40):
        rows = []
        for i in range(n):
            m = f"N{i}"
            rows += [create(1000 + i * 50, mint=m), trade(8000 + i * 50, "a", mint=m), trade(9000 + i * 50, "b", mint=m)]
        rows += [trade(200_000 + i * 50, "c", mint=f"N{i}") for i in range(n)]
        return sorted(rows, key=lambda r: r[0])

    def test_random_is_seeded_and_reproducible(self):
        rows = self.new_coins()
        a, b = run(rows, BaseRandom())[0], run(rows, BaseRandom())[0]
        self.assertEqual(decisions(a), decisions(b))
        entered = {f.mint for f in fills(a, "buy")}
        self.assertTrue(0 < len(entered) < 40)
        expected = {f"N{i}" for i in range(40) if unit_hash(BaseRandom.seed, f"N{i}") < BaseRandom.enter_prob}
        self.assertEqual(entered, expected)

    def test_random_other_seed_differs(self):
        class Other(BaseRandom):
            name, seed = "base_random2", 1
        a, b = run(self.new_coins(), BaseRandom())[0], run(self.new_coins(), Other())[0]
        self.assertNotEqual({f.mint for f in fills(a, "buy")}, {f.mint for f in fills(b, "buy")})

    def test_hold60_buys_at_fixed_age_and_sells_after_60s(self):
        rows = [create(1000), trade(3000, "a"), trade(7000, "b")] + [trade(7000 + 5000 * k, "c") for k in range(1, 20)]
        book, _ = run(rows, BaseHold60())
        buys, sells = fills(book, "buy"), fills(book, "sell")
        self.assertEqual(len(buys), 1)
        self.assertEqual(buys[0].decision_ms, 7000)           # first trade at age >= 5 s
        self.assertEqual(len(sells), 1)
        held = sells[0].decision_ms - buys[0].arrival_ms
        self.assertGreaterEqual(held, 60_000)
        self.assertLess(held, 62_000)

    def test_elite_copy_follows_buy_and_sell(self):
        rows = [create(1000), trade(3000, "a"), trade(5000, "E1", sol=2.0), trade(8000, "b"),
                trade(20_000, "E1", "sell", sol=2.0), trade(23_000, "c")]
        book, _ = run(rows, BaseEliteCopy(), elite_names={"E1": "Decu"})
        buys, sells = fills(book, "buy"), fills(book, "sell")
        self.assertEqual((len(buys), buys[0].decision_ms, buys[0].reason), (1, 5000, "copy Decu"))
        self.assertEqual((len(sells), sells[0].decision_ms, sells[0].reason), (1, 20_000, "Decu sold"))
        none, _ = run(rows, BaseEliteCopy())                  # nobody is an elite: no copy
        self.assertEqual(none.fill_log, [])

    def test_elite_copy_ignores_other_elites_sell(self):
        rows = [create(1000), trade(5000, "E1", sol=2.0), trade(8000, "b"), trade(12_000, "E2", "sell"),
                trade(15_000, "c")]
        book, _ = run(rows, BaseEliteCopy(), elite_names={"E1": "Decu", "E2": "Theo"})
        self.assertEqual(fills(book, "sell"), [])
        self.assertIn("M", book.positions)


class LoaderTest(unittest.TestCase):
    def test_names_unique_and_params_are_class_attributes(self):
        algos = [MrFrog, Smokez, FrankDegods, BaseRandom, BaseHold60, BaseEliteCopy]
        names = [a.name for a in algos]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(Tracked.name, Strategy.name)        # helper base is never loaded as an algo
        for a in (MrFrog, Smokez, FrankDegods):
            for p in ("size_frac", "max_price_impact", "stop_loss", "daily_kill_dd", "max_exposure_frac", "max_positions"):
                self.assertIsNotNone(getattr(a, p), f"{a.name}.{p}")


if __name__ == "__main__":
    unittest.main()
