"""History fetcher: paced RPC, swap derivation, trips, monthly buckets, resume. No network."""
import json
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from gemtracker import history, net
from tests.helpers import SOL, addr

W = addr("wallet")
COIN = addr("coin")
COIN2 = addr("coin2")
ATA = addr("wallet-ata")
WSOL_ACC = addr("wallet-wsol")
POOL = addr("pool")


def ts(text):
    return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp())


def json_tx(sig, *, wallet_delta, accounts=(), program=history.PUMP, loaded_program=None, err=None,
            payer=W, slot=100, block_time=1_790_000_000, fee=5000):
    """getTransaction result in "json" encoding.

    accounts: (key, owner, mint, pre_raw, post_raw, pre_lamports, post_lamports); pre_raw None = created."""
    keys = [payer] + ([W] if payer != W else []) + [a[0] for a in accounts] + [POOL, program]
    w_index = keys.index(W)
    pre = [10 * SOL] * len(keys)
    post = list(pre)
    post[w_index] += wallet_delta
    pre_tok, post_tok = [], []
    for a in accounts:
        key, owner, mint, pre_raw, post_raw, pre_lam, post_lam = a
        i = keys.index(key)
        pre[i], post[i] = pre_lam, post_lam
        row = lambda raw: {"accountIndex": i, "mint": mint, "owner": owner, "programId": "Tokenkeg",
                           "uiTokenAmount": {"amount": str(raw), "decimals": 9 if mint == history.WSOL else 6}}
        if pre_raw is not None:
            pre_tok.append(row(pre_raw))
        if post_raw is not None:
            post_tok.append(row(post_raw))
    instructions = [{"programIdIndex": len(keys) - 1, "accounts": [], "data": ""}]
    loaded = {"writable": [], "readonly": []}
    inner = []
    if loaded_program:
        loaded["readonly"] = [loaded_program]
        instructions = [{"programIdIndex": len(keys), "accounts": [], "data": ""}]
        inner = [{"index": 0, "instructions": [{"programIdIndex": len(keys) - 1, "accounts": [], "data": ""}]}]
    return {"slot": slot, "blockTime": block_time, "transactionIndex": 3,
            "meta": {"err": err, "fee": fee, "preBalances": pre, "postBalances": post,
                     "preTokenBalances": pre_tok, "postTokenBalances": post_tok,
                     "loadedAddresses": loaded, "innerInstructions": inner},
            "transaction": {"signatures": [sig], "message": {"accountKeys": keys, "instructions": instructions}}}


RENT = 2_039_280


def pump_buy(sig, sol=1.0, raw=1_000_000_000, **kw):
    # wallet pays SOL + fee + rent for its new token account
    return json_tx(sig, wallet_delta=-int(sol * SOL) - 5000 - RENT,
                   accounts=[(ATA, W, COIN, None, raw, 0, RENT)], **kw)


def pump_sell(sig, sol=1.5, raw_before=1_000_000_000, raw_after=0, **kw):
    return json_tx(sig, wallet_delta=int(sol * SOL) - 5000,
                   accounts=[(ATA, W, COIN, raw_before, raw_after, RENT, RENT)], **kw)


class DeriveSwapsTest(unittest.TestCase):
    def test_buy_nets_out_rent_and_fee(self):
        kind, rows, owned = history.derive_swaps(pump_buy("s1"), W)
        self.assertEqual(kind, "swap")
        (r,) = rows
        self.assertEqual((r["side"], r["mint"], r["sol"], r["tokens"], r["venue"]), ("buy", COIN, 1.0, 1000.0, "pump"))
        self.assertAlmostEqual(r["fee_sol"], 0.000005)
        self.assertAlmostEqual(r["rent_sol"], RENT / SOL)
        self.assertEqual(owned, {ATA: COIN})

    def test_sell(self):
        kind, rows, _ = history.derive_swaps(pump_sell("s2", program=history.PUMP_AMM), W)
        self.assertEqual(kind, "swap")
        self.assertEqual((rows[0]["side"], rows[0]["sol"], rows[0]["tokens"], rows[0]["venue"]),
                         ("sell", 1.5, 1000.0, "pumpswap"))

    def test_failed_tx_skipped(self):
        kind, rows, _ = history.derive_swaps(pump_buy("s3", err={"InstructionError": [0, "Custom"]}), W)
        self.assertEqual((kind, rows), ("failed", []))

    def test_non_swaps_ignored(self):
        transfer = json_tx("t1", wallet_delta=-2 * SOL - 5000, program="11111111111111111111111111111111")
        self.assertEqual(history.derive_swaps(transfer, W)[0], "nonswap")
        # coins arrive with no SOL paid: an airdrop / transfer in, not a buy
        gift = json_tx("t2", wallet_delta=-5000, accounts=[(ATA, W, COIN, 0, 500, RENT, RENT)])
        self.assertEqual(history.derive_swaps(gift, W)[0], "nonswap")
        self.assertEqual(history.derive_swaps(None, W)[0], "missing")

    def test_wsol_counts_as_sol_and_aggregator_venue_from_lookup_table(self):
        # sell into wrapped SOL: the wallet pays fee + rent of a new WSOL account, the proceeds land there
        tx = json_tx("w1", wallet_delta=-5000 - RENT, loaded_program=history.JUPITER, accounts=[
            (ATA, W, COIN, 2_000_000, 0, RENT, RENT),
            (WSOL_ACC, W, history.WSOL, None, int(0.75 * SOL), 0, RENT + int(0.75 * SOL))])
        kind, rows, owned = history.derive_swaps(tx, W)
        self.assertEqual(kind, "swap")
        self.assertEqual((rows[0]["side"], rows[0]["mint"], rows[0]["sol"], rows[0]["venue"]),
                         ("sell", COIN, 0.75, "jupiter"))
        self.assertAlmostEqual(rows[0]["rent_sol"], RENT / SOL)
        self.assertEqual(owned[WSOL_ACC], history.WSOL)

    def test_wsol_closed_after_buy(self):
        # wrap 1 SOL, buy, close the WSOL account: net -1 SOL, rent comes back
        tx = json_tx("w2", wallet_delta=-int(1 * SOL) - 5000, accounts=[
            (ATA, W, COIN, 0, 10_000, RENT, RENT),
            (WSOL_ACC, W, history.WSOL, 0, None, RENT, 0)])
        tx["meta"]["postBalances"][tx["transaction"]["message"]["accountKeys"].index(W)] += RENT
        kind, rows, _ = history.derive_swaps(tx, W)
        self.assertEqual((kind, rows[0]["side"], rows[0]["sol"]), ("swap", "buy", 1.0))

    def test_fee_not_added_when_someone_else_pays(self):
        tx = pump_sell("p1", sol=1.0, payer=addr("relayer"))
        tx["meta"]["postBalances"][1] += 5000  # the wallet did not pay the fee
        _, rows, _ = history.derive_swaps(tx, W)
        self.assertEqual((rows[0]["sol"], rows[0]["fee_sol"]), (1.0, 0.0))

    def test_multi_mint_and_stable_skipped(self):
        tx = json_tx("m1", wallet_delta=-SOL, accounts=[(ATA, W, COIN, 0, 5, 0, 0),
                                                        (addr("a2"), W, COIN2, 0, 7, 0, 0)])
        self.assertEqual(history.derive_swaps(tx, W)[0], "multi_mint")
        usdc = next(iter(history.STABLES))
        tx = json_tx("m2", wallet_delta=-SOL, accounts=[(ATA, W, usdc, 0, 5, 0, 0)])
        self.assertEqual(history.derive_swaps(tx, W)[0], "other_asset")


def swap(sig, slot, side, sol, tokens, mint=COIN, t=None):
    return {"slot": slot, "block_time": t if t is not None else 1_790_000_000 + slot, "tx_index": 0, "sig": sig,
            "mint": mint, "side": side, "sol": sol, "tokens": tokens, "fee_sol": 0.00001, "venue": "pump"}


class TripsTest(unittest.TestCase):
    def test_flat_to_flat_trips_open_bags_and_orphans(self):
        swaps = [
            swap("a", 1, "buy", 1.0, 1000), swap("b", 2, "buy", 1.0, 500),
            swap("c", 3, "sell", 1.2, 750), swap("d", 4, "sell", 1.5, 749.5),  # dust left: closed
            swap("d", 4, "sell", 1.5, 749.5),                                   # duplicate row ignored
            swap("e", 5, "buy", 0.5, 100), swap("f", 6, "sell", 0.2, 100),      # second trip, a loss
            swap("g", 7, "buy", 2.0, 10, mint=COIN2), swap("h", 8, "sell", 1.0, 5, mint=COIN2),  # still open
            swap("i", 9, "sell", 0.3, 50, mint=addr("gift")),                   # never bought
        ]
        trips, bags, orphans = history.build_trips(list(reversed(swaps)), "decu")
        self.assertEqual([(t["sol_in"], t["sol_out"], t["pnl_sol"]) for t in trips],
                         [(2.0, 2.7, 0.7), (0.5, 0.2, -0.3)])
        self.assertEqual((trips[0]["n_buys"], trips[0]["n_sells"], trips[0]["hold_s"]), (2, 2, 3.0))
        self.assertEqual(len(bags), 1)
        self.assertEqual((bags[0]["mint"], bags[0]["tokens_left"], bags[0]["cost_left"], bags[0]["status"]),
                         (COIN2, 5, 1.0, "unrealized-unknown"))
        self.assertEqual((orphans["n"], orphans["sol"]), (1, 0.3))


class MonthlyTest(unittest.TestCase):
    def test_et_month_boundary(self):
        # 03:30 UTC Nov 1 = 23:30 EDT Oct 31; 04:30 UTC = 00:30 EDT Nov 1
        before, after = ts("2026-11-01T03:30:00"), ts("2026-11-01T04:30:00")
        swaps = [swap("a", 1, "buy", 1.0, 100, t=before - 60), swap("b", 2, "sell", 2.0, 100, t=before),
                 swap("c", 3, "buy", 1.0, 100, t=after - 60), swap("d", 4, "sell", 0.5, 100, t=after),
                 swap("e", 5, "buy", 3.0, 100, mint=COIN2, t=after)]
        trips, bags, orphans = history.build_trips(swaps)
        months = history.monthly_summary(trips, bags, orphans, {"2026-10": 200.0})
        self.assertEqual(sorted(months), ["2026-10", "2026-11"])
        oct_, nov = months["2026-10"], months["2026-11"]
        self.assertEqual((oct_["pnl_sol"], oct_["deployed_sol"], oct_["return_per_sol"], oct_["win_rate"]),
                         (1.0, 1.0, 1.0, 1.0))
        self.assertEqual(oct_["pnl_usd_approx"], 200.0)
        self.assertEqual((nov["pnl_sol"], nov["trips"], nov["win_rate"], nov["open_bags"], nov["open_bag_sol_in"]),
                         (-0.5, 1, 0.0, 1, 3.0))
        self.assertNotIn("pnl_usd_approx", nov)


class FakeClock:
    def __init__(self):
        self.t = 1000.0
        self.sleeps = []

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s

    def __call__(self):
        return self.t


class PacedRpcTest(unittest.TestCase):
    def rpc(self, replies):
        clock = FakeClock()
        replies = list(replies)

        def post(url, body):
            r = replies.pop(0)
            if isinstance(r, Exception):
                raise r
            return r

        logs = []
        return history.PacedRpc("https://api.mainnet.solana.com", rps=2, post=post, sleep=clock.sleep,
                                clock=clock, rng=lambda: 0.5, log=logs.append), clock, logs

    def test_413_pauses_ten_minutes_then_continues(self):
        rpc, clock, logs = self.rpc([net.HttpError(413, "u", "data allowance exceeded"), {"result": 7}])
        self.assertEqual(rpc.call("getSlot", []), 7)
        self.assertGreaterEqual(max(clock.sleeps), 600)
        self.assertEqual((rpc.stats["413"], rpc.stats["requests"]), (1, 2))
        self.assertAlmostEqual(rpc.interval, 1.0)  # pace halved to 1 req/s
        self.assertTrue(any("413" in line for line in logs))

    def test_allowance_error_in_body_and_growing_pauses(self):
        err = {"error": {"code": -32000, "message": "Your data allowance has been used up"}}
        rpc, clock, _ = self.rpc([err, err, {"result": 1}])
        rpc.call("getSlot", [])
        pauses = [s for s in clock.sleeps if s >= 600]
        self.assertEqual(pauses, [600, 1200])

    def test_429_backoff_with_jitter_and_pacing(self):
        rpc, clock, _ = self.rpc([net.HttpError(429, "u"), net.HttpError(503, "u"), {"result": 1},
                                  {"result": 2}])
        self.assertEqual(rpc.call("getSlot", []), 1)
        self.assertIn(2.0, clock.sleeps)   # attempt 0: 2s x (0.5 + 0.5)
        self.assertIn(4.0, clock.sleeps)   # attempt 1: 4s
        self.assertEqual((rpc.stats["429"], rpc.stats["5xx"]), (1, 1))
        start = clock.t
        rpc.call("getSlot", [])
        self.assertGreaterEqual(clock.t - start, 0.5 - 1e-9)  # never faster than the pace

    def test_missing_tx_codes_return_none_and_paid_urls_refused(self):
        rpc, _, _ = self.rpc([{"error": {"code": -32009, "message": "not available"}}])
        self.assertIsNone(rpc.call("getTransaction", ["x"]))
        with self.assertRaises(ValueError):
            history.PacedRpc("https://mainnet.helius-rpc.com/?api-key=abc")


class FakeChain:
    """getSignaturesForAddress + getTransaction over in-memory data."""

    def __init__(self, sigs_by_address, txs, on_call=None):
        self.sigs = sigs_by_address  # address -> infos, newest first
        self.txs = txs
        self.calls = []
        self.stats = Counter()
        self.on_call = on_call

    def rate(self):
        return 2.0

    def call(self, method, params):
        self.calls.append((method, params))
        self.stats["requests"] += 1
        if self.on_call:
            self.on_call(self)
        if method == "getTransaction":
            return self.txs.get(params[0])
        address, cfg = params
        infos = self.sigs.get(address, [])
        if cfg.get("before"):
            infos = infos[[s["signature"] for s in infos].index(cfg["before"]) + 1:]
        return infos[:cfg["limit"]]


def infos(prefix, n, slot0=10_000, fail_every=0):
    return [{"signature": f"{prefix}{i}", "slot": slot0 - i, "blockTime": 1_790_000_000 - i, "transactionIndex": 0,
             "err": {"x": 1} if fail_every and i % fail_every == 0 else None} for i in range(n)]


class FetcherTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "decu"

    def tearDown(self):
        self.tmp.cleanup()

    def test_pagination_and_resume_after_stop(self):
        sigs = infos("s", 2500, fail_every=5)
        txs = {s["signature"]: pump_buy(s["signature"], slot=s["slot"]) for s in sigs}
        stop = self.dir / "STOP"

        def stop_after_two_pages(chain):
            if sum(1 for m, _ in chain.calls if m == "getSignaturesForAddress") == 2:
                stop.touch()

        chain1 = FakeChain({W: sigs}, txs, on_call=stop_after_two_pages)
        f1 = history.Fetcher("Decu", W, chain1, self.dir, mode="wallet", log=lambda m: None)
        self.assertFalse(f1.run())
        self.assertEqual(f1.state["feeds"][W]["before"], "s1999")
        stop.unlink()

        chain2 = FakeChain({W: sigs}, txs)
        f2 = history.Fetcher("Decu", W, chain2, self.dir, mode="wallet", log=lambda m: None)
        self.assertTrue(f2.run())
        pages = [p for m, p in chain2.calls if m == "getSignaturesForAddress"]
        self.assertEqual([p[1].get("before") for p in pages], ["s1999"])  # resumed, not restarted
        fetched = [p[0] for m, p in chain2.calls if m == "getTransaction"]
        self.assertEqual(len(fetched), 2000)          # 2500 minus 500 failed, each once
        self.assertEqual(fetched[0], "s1")            # newest first
        self.assertEqual(f2.state["counts"]["swap"], 2000)
        lines = (self.dir / "sigs.jsonl").read_text().splitlines()
        self.assertEqual(sum(len(json.loads(x)["sigs"]) for x in lines), 2500)

        # every successful signature is recorded once and the reports are final
        processed = (self.dir / "processed.txt").read_text().split()
        self.assertEqual(len(processed), 2000)
        summary = json.loads((self.dir / "monthly.json").read_text())
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["open_bags"]["n"], 1)

    def test_resume_mid_transactions_and_until_slot(self):
        sigs = infos("s", 30)
        txs = {s["signature"]: pump_buy(s["signature"], slot=s["slot"]) for s in sigs}
        stop = self.dir / "STOP"

        def stop_after_ten_txs(chain):
            if sum(1 for m, _ in chain.calls if m == "getTransaction") == 10:
                stop.touch()

        f1 = history.Fetcher("Decu", W, FakeChain({W: sigs}, txs, stop_after_ten_txs), self.dir, mode="wallet",
                             until_slot=10_000 - 19, log=lambda m: None)
        self.assertFalse(f1.run())
        stop.unlink()
        chain2 = FakeChain({W: sigs}, txs)
        f2 = history.Fetcher("Decu", W, chain2, self.dir, mode="wallet", until_slot=10_000 - 19, log=lambda m: None)
        self.assertTrue(f2.run())
        fetched = [p[0] for m, p in chain2.calls if m == "getTransaction"]
        self.assertEqual(fetched, [f"s{i}" for i in range(10, 20)])  # slots below until_slot never fetched

    def test_auto_picks_via_for_a_spammed_wallet_and_expands_token_accounts(self):
        pump_uva, amm_uva = history.accumulators(W)
        spam = [{"signature": f"x{i}", "slot": 9000, "blockTime": 1_790_000_000, "err": None} for i in range(1000)]
        buy = {"signature": "b1", "slot": 500, "blockTime": 1_790_000_000, "transactionIndex": 0, "err": None}
        sell = {"signature": "s1", "slot": 600, "blockTime": 1_790_000_100, "transactionIndex": 0, "err": None}
        chain = FakeChain({W: spam, pump_uva: [buy], amm_uva: [], ATA: [sell, buy]},
                          {"b1": pump_buy("b1", slot=500, block_time=1_790_000_000),
                           "s1": pump_sell("s1", slot=600, block_time=1_790_000_100, program=history.JUPITER)})
        f = history.Fetcher("Decu", W, chain, self.dir, log=lambda m: None)
        self.assertTrue(f.run())
        self.assertEqual(f.state["mode"], "via")
        self.assertEqual(set(f.state["feeds"]), {pump_uva, amm_uva})
        fetched = [p[0] for m, p in chain.calls if m == "getTransaction"]
        self.assertEqual(fetched, ["b1", "s1"])  # the buy once, the sell found via the token account
        trips = [json.loads(x) for x in (self.dir / "trips.jsonl").read_text().splitlines()]
        self.assertEqual([(t["pnl_sol"], t["venue"]) for t in trips], [(0.5, "pump")])


if __name__ == "__main__":
    unittest.main()
