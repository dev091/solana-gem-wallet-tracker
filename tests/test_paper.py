"""Decoders, market state, paper fills, tape and replay used by the live paper runner."""
import base64
import gzip
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from gemtracker import chain_events as ce
from gemtracker.live import pick_recycle
from gemtracker.market import Market
from gemtracker.papersim import PaperSim, SimConfig, buy_out, sell_out
from gemtracker.replay import replay, row_to_event
from gemtracker.strategy import Buy, Sell, Strategy
from gemtracker.tape import TapeWriter, event_row, read_tape


def key(tag: str) -> bytes:
    return hashlib.sha256(tag.encode()).digest()


def borsh(spec, values: dict) -> bytes:
    out = b""
    for name, kind in spec:
        if name not in values:
            break
        v = values[name]
        if kind == "key":
            out += v
        elif kind in ("u64", "i64"):
            out += struct.pack("<Q" if kind == "u64" else "<q", v)
        elif kind == "u16":
            out += struct.pack("<H", v)
        elif kind in ("u8", "bool"):
            out += bytes([int(v)])
        elif kind == "string":
            out += struct.pack("<I", len(v)) + v.encode()
        elif kind == "shareholders":
            out += struct.pack("<I", len(v)) + b"".join(v)
        else:
            raise AssertionError(kind)
    return out


def data_line(name: str, spec, values) -> str:
    return "Program data: " + base64.b64encode(ce.disc(name) + borsh(spec, values)).decode()


def invoked(program: str, *lines, depth=1):
    return [f"Program {program} invoke [{depth}]", *lines, f"Program {program} success"]


VSOL, VTOK = 40 * 10 ** 9, 800_000_000 * 10 ** 6


def pump_trade(**over):
    v = {"mint": key("mint"), "sol_amount": 10 ** 9, "token_amount": 25_000_000 * 10 ** 6,
         "is_buy": True, "user": key("user"), "timestamp": 1_791_000_000,
         "virtual_sol_reserves": VSOL, "virtual_token_reserves": VTOK, "real_sol_reserves": 10 * 10 ** 9,
         "real_token_reserves": ce.PUMP_INITIAL_REAL_TOKENS // 2, "fee_recipient": key("fee"),
         "fee_basis_points": 95, "fee": 0, "creator": key("dev"), "creator_fee_basis_points": 30,
         "creator_fee": 0, "track_volume": False, "total_unclaimed_tokens": 0, "total_claimed_tokens": 0,
         "current_sol_volume": 0, "last_update_timestamp": 0, "ix_name": "buy", "mayhem_mode": False,
         "cashback_fee_basis_points": 0, "cashback": 0, "buyback_fee_basis_points": 0, "buyback_fee": 0,
         "shareholders": [b"\x01" * 34], "quote_mint": bytes(32), "quote_amount": 0,
         "virtual_quote_reserves": 0, "real_quote_reserves": 0}
    v.update(over)
    return data_line("TradeEvent", ce.PUMP_TRADE, v)


class DecoderTest(unittest.TestCase):
    def test_pump_trade_full_layout(self):
        (ev,) = ce.parse_logs("sig", invoked(ce.PUMP, pump_trade()), 5)
        self.assertEqual((ev.kind, ev.venue, ev.side, ev.slot), ("trade", "pump", "buy", 5))
        self.assertEqual(ev.mint, ce.b58encode(key("mint")))
        self.assertAlmostEqual(ev.price, (VSOL / 1e9) / (VTOK / 1e6))
        self.assertEqual((ev.reserve_quote, ev.reserve_base, ev.fee_bps), (VSOL, VTOK, 125))
        self.assertAlmostEqual(ev.progress, 0.5)
        self.assertEqual(ev.quote_mint, ce.WSOL)  # default key means SOL

    def test_old_short_layout_still_decodes(self):
        short = {k: v for k, v in [("mint", key("m")), ("sol_amount", 1), ("token_amount", 1),
                                   ("is_buy", False), ("user", key("u")), ("timestamp", 1),
                                   ("virtual_sol_reserves", VSOL), ("virtual_token_reserves", VTOK),
                                   ("real_sol_reserves", 1), ("real_token_reserves", 1)]}
        (ev,) = ce.parse_logs("s", invoked(ce.PUMP, data_line("TradeEvent", ce.PUMP_TRADE, short)))
        self.assertEqual(ev.side, "sell")

    def test_events_attributed_by_invoke_stack(self):
        router = "Router1111111111111111111111111111111111111"
        logs = invoked(router, *invoked(ce.PUMP, pump_trade(), depth=2),
                       pump_trade())  # emitted by the router after pump returned: not pump's
        self.assertEqual(len(ce.parse_logs("s", logs)), 1)
        self.assertEqual(ce.parse_logs("s", [pump_trade()]), [])  # no invoke at all

    def test_create_records_supply_and_mayhem(self):
        v = {"name": "Cat", "symbol": "CAT", "uri": "u", "mint": key("m"), "bonding_curve": key("bc"),
             "user": key("u"), "creator": key("u"), "timestamp": 7, "virtual_token_reserves": VTOK,
             "virtual_sol_reserves": VSOL, "real_token_reserves": 1, "token_total_supply": 2 * 10 ** 15,
             "token_program": key("tp"), "is_mayhem_mode": True}
        (ev,) = ce.parse_logs("s", invoked(ce.PUMP, data_line("CreateEvent", ce.PUMP_CREATE, v)))
        self.assertEqual((ev.kind, ev.extra["supply"], ev.extra["mayhem"]), ("create", 2 * 10 ** 9, True))


def trade_ev(mint="M", side="buy", sol=1.0, rq=VSOL, rb=VTOK, user="u", ts=0, venue="pump"):
    return ce.ChainEvent("trade", venue, "sig", 0, ts=ts, mint=mint, user=user, side=side,
                         quote=int(sol * 1e9), tokens=10 ** 6, price=(rq / 1e9) / (rb / 1e6),
                         reserve_quote=rq, reserve_base=rb, fee_bps=100)


class MarketTest(unittest.TestCase):
    def test_window_counts_only_recent_trades(self):
        m = Market()
        m.apply(trade_ev(user="a"), 1_000)
        m.apply(trade_ev(user="b"), 20_000)
        m.apply(trade_ev(user="b", side="sell", sol=0.5), 21_000)
        w = m.get("M").window(21_000, 5)
        self.assertEqual((w["buys"], w["sells"], w["unique_buyers"]), (1, 1, 1))
        self.assertAlmostEqual(w["net_sol"], 0.5)

    def test_late_trade_keeps_window_in_time_order(self):
        m = Market()
        m.apply(trade_ev(user="a", sol=1.0), 10_000)
        m.apply(trade_ev(user="b", sol=2.0), 30_000)
        m.apply(trade_ev(user="c", sol=4.0), 26_000)  # parked event applied late
        self.assertEqual([t.rx for t in m.get("M").trades], [10_000, 26_000, 30_000])
        w = m.get("M").window(30_000, 5)
        self.assertEqual((w["buys"], w["unique_buyers"]), (2, 2))
        self.assertAlmostEqual(w["buy_sol"], 6.0)

    def test_window_can_leave_out_named_wallets(self):
        m = Market()
        m.apply(trade_ev(user="decu", sol=5.0), 10_000)
        m.apply(trade_ev(user="b", sol=1.0), 11_000)
        w = m.get("M").window(11_000, 5, exclude=frozenset({"decu"}))
        self.assertEqual((w["buys"], w["unique_buyers"], w["buy_sol"]), (1, 1, 1.0))
        self.assertEqual(m.get("M").window(11_000, 5)["buys"], 2)  # the cache keeps them apart

    def test_holder_stats_follow_new_trades(self):
        m = Market()
        m.apply(trade_ev(user="a"), 1_000)
        st = m.get("M")
        self.assertEqual(st.holder_count(), 1)
        m.apply(trade_ev(user="b"), 2_000)
        self.assertEqual(st.holder_count(), 2)
        m.apply(trade_ev(user="a", side="sell"), 3_000)
        self.assertEqual(st.holder_count(), 1)

    def test_create_makes_coin_tradable(self):
        m = Market()
        ev = ce.ChainEvent("create", "pump", "s", 0, ts=1, mint="N", user="d", price=1e-7,
                           reserve_quote=VSOL, reserve_base=VTOK, extra={"creator": "d"})
        st = m.apply(ev, 1_000)
        self.assertEqual((st.reserve_quote, st.fee_bps), (VSOL, 125))


class OneShot(Strategy):
    name = "oneshot"

    def __init__(self, sell_after_ms=None, slip=0.25):
        self.sell_after_ms, self.slip, self.done, self.fills = sell_after_ms, slip, False, []

    def on_trade(self, st, ev, now_ms, book):
        if not self.done:
            self.done = True
            return [Buy(st.mint, 0.1, "test", max_slippage=self.slip)]
        return []

    def on_tick(self, market, now_ms, book):
        if self.sell_after_ms and book.positions and now_ms >= self.sell_after_ms:
            return [Sell(m) for m in book.positions]
        return []

    def on_fill(self, fill, book):
        self.fills.append(fill)


def run(rows_events, strat, latency=1000):
    """rows_events: list of (rx, ChainEvent); same order of operations as the live runner."""
    rows = [dict(event_row(ev, rx)) for rx, ev in rows_events]
    return replay([strat], SimConfig(latency_ms=latency, venue_latency_ms={}), rows, 100.0)


class PaperSimTest(unittest.TestCase):
    def test_constant_product_round_trip_loses_only_fees(self):
        tokens, fee_in = buy_out(1.0, 0, VSOL, VTOK)
        back, fee_out = sell_out(tokens, 0, VSOL + 10 ** 9, VTOK - int(tokens * 1e6))
        self.assertAlmostEqual(back, 1.0, places=6)
        self.assertEqual((fee_in, fee_out), (0, 0))

    def test_fill_uses_state_at_arrival_not_decision(self):
        s = OneShot()
        # decision at rx 1000 (price p0); a big buy lands at 1500 before our arrival at 2000
        sim, market = run([(1_000, trade_ev(rq=VSOL, rb=VTOK)),
                           (1_500, trade_ev(rq=VSOL * 11 // 10, rb=VTOK * 10 // 11)),
                           (2_500, trade_ev(rq=VSOL * 12 // 10, rb=VTOK * 10 // 12))], s)
        f = s.fills[0]
        self.assertEqual(f.status, "filled")
        self.assertAlmostEqual(f.price, (VSOL * 1.1 / 1e9) / (VTOK / 1.1 / 1e6), places=12)
        self.assertGreater(f.price, f.decision_price)

    def test_slippage_rejection_still_pays_network_fee(self):
        s = OneShot(slip=0.05)
        sim, market = run([(1_000, trade_ev()), (1_500, trade_ev(rq=VSOL * 2, rb=VTOK // 2))], s)
        book = sim.books["oneshot"]
        self.assertEqual((s.fills[0].status, book.positions), ("rejected", {}))
        self.assertAlmostEqual(book.cash_sol, book.start_sol - SimConfig.tx_fee_sol)
        self.assertTrue(s.fills[0].why.startswith("slippage"))

    def test_position_only_after_fill_and_cash_conserved(self):
        s = OneShot(sell_after_ms=5_000)
        sim, market = run([(1_000, trade_ev()), (1_200, trade_ev()), (4_000, trade_ev()),
                           (6_500, trade_ev())], s)
        book = sim.books["oneshot"]
        buy, sell = s.fills
        self.assertEqual((buy.side, sell.side, buy.status, sell.status), ("buy", "sell", "filled", "filled"))
        self.assertEqual(book.positions, {})
        expected = book.start_sol - buy.sol - buy.tx_fee_sol + sell.sol - sell.tx_fee_sol
        self.assertAlmostEqual(book.cash_sol, expected, places=12)
        self.assertGreater(buy.venue_fee_sol, 0)
        self.assertAlmostEqual(book.closed[0]["pnl_sol"], sell.sol - sell.tx_fee_sol - buy.sol - buy.tx_fee_sol,
                               places=12)

    def test_coin_quoted_in_another_token_is_never_bought(self):
        s = OneShot()
        usdc = trade_ev()
        usdc.quote_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        sim, market = run([(1_000, usdc), (3_000, trade_ev())], s)
        self.assertEqual((s.fills, sim.books["oneshot"].positions), ([], {}))
        self.assertEqual(market.get("M").quote_mint, ce.WSOL)  # a later SOL-quoted trade resets it

    def test_adds_only_when_asked_and_one_buy_in_flight(self):
        class Adder(OneShot):
            name = "oneshot"

            def __init__(self, add):
                super().__init__()
                self.add, self.n = add, 0

            def on_trade(self, st, ev, now_ms, book):
                self.n += 1
                self.equity = book.equity()
                return [Buy(st.mint, 0.1, add=self.add)]   # asks on every trade
        for add, buys in ((False, 1), (True, 2)):
            s = Adder(add)
            # trades at 1000 and 1500: the second buy is dropped while the first is in flight;
            # at 3000 the first has filled, so only an add can go in
            sim, _ = run([(1_000, trade_ev()), (1_500, trade_ev()), (3_000, trade_ev()), (3_100, trade_ev())], s)
            self.assertEqual([f.side for f in s.fills], ["buy"] * buys, add)
            self.assertEqual(sim.books["oneshot"].positions["M"].buys, buys)
        f = s.fills[0]
        self.assertGreater(f.exec_price, f.price)  # average paid includes fee and price impact
        self.assertAlmostEqual(f.exec_price, f.sol / f.tokens)
        self.assertLess(s.equity, sim.books["oneshot"].start_sol)  # liquidation value after costs

    def test_one_broken_algo_does_not_stop_others(self):
        class Broken(Strategy):
            name = "broken"

            def on_trade(self, *a):
                raise ValueError("boom")
        good = OneShot()
        rows = [event_row(trade_ev(), 1_000), event_row(trade_ev(), 3_000)]
        sim, _ = replay([Broken(), good], SimConfig(latency_ms=1000, venue_latency_ms={}), rows, 100.0)
        self.assertEqual(sim.books["oneshot"].fills, 1)


class TapeTest(unittest.TestCase):
    def test_round_trip_and_manifest(self):
        ev = trade_ev(ts=5)
        with tempfile.TemporaryDirectory() as d:
            w = TapeWriter(Path(d))
            w.write(event_row(ev, 1_791_000_000_000))
            w.close()
            rows = list(read_tape(Path(d)))
            manifest = json.loads((Path(d) / "manifest.jsonl").read_text())
            path = Path(d) / manifest["file"]
            self.assertEqual(manifest["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            with gzip.open(path, "rt") as fh:
                self.assertEqual(len(fh.readlines()), 1)
        back = row_to_event(rows[0])
        for f in ("kind", "venue", "mint", "side", "quote", "reserve_quote", "reserve_base", "fee_bps",
                  "price", "ts"):
            self.assertEqual(getattr(back, f), getattr(ev, f), f)

    def test_half_written_last_line_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "20261007").mkdir()
            with gzip.open(Path(d) / "20261007" / "18.jsonl.gz", "wt", encoding="utf-8") as fh:
                fh.write('{"a": 1}\n{"a": 2}\n{"a": ')
            self.assertEqual(list(read_tape(Path(d))), [{"a": 1}, {"a": 2}])


class RecycleTest(unittest.TestCase):
    def test_slowest_connection_per_stream_is_recycled(self):
        wins = {"pump@mb0": 300, "pump@mb1": 90, "pump@mb2": 10, "pump@sc3": 100,
                "pumpswap@mb0": 500, "pumpswap@mb1": 400,     # both pull their weight
                "launchlab@mb0": 30, "launchlab@sc1": 0}       # too few tx to judge
        self.assertEqual(pick_recycle(wins), ["pump@mb2"])

    def test_missing_connection_is_not_judged(self):
        self.assertEqual(pick_recycle({"pumpswap@mb0": 900}), [])


if __name__ == "__main__":
    unittest.main()
