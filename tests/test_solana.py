import unittest

from gemtracker.config import SOL_MINT
from gemtracker.solana import History, SolanaRpc, delta_from_helius_tx, delta_from_rpc_tx, fetch_history
from tests.helpers import SOL, addr, rpc_tx

WALLET = addr("wallet")
MINT = addr("meme")
OTHER = addr("someone-else")


class RpcDeltaTest(unittest.TestCase):
    def test_pump_buy_pays_sol_receives_tokens(self):
        tx = rpc_tx(WALLET, "sig-buy", 1_700_000_000, sol_before=10 * SOL, sol_after=8_497_995_000,
                    post_tokens=[(MINT, 35_000_000_000_000, 6)])
        d = delta_from_rpc_tx(tx, WALLET)
        self.assertEqual(d.signature, "sig-buy")
        self.assertEqual(d.ts, 1_700_000_000)
        self.assertAlmostEqual(d.sol, -1.502005)
        self.assertEqual(d.tokens, {MINT: 35_000_000.0})

    def test_wrapped_sol_counts_as_sol(self):
        tx = rpc_tx(WALLET, "sig", 1, sol_before=5 * SOL, sol_after=5 * SOL - 5000,
                    pre_tokens=[(SOL_MINT, 2 * SOL, 9)], post_tokens=[(SOL_MINT, 0, 9), (MINT, 1_000_000, 6)])
        d = delta_from_rpc_tx(tx, WALLET)
        self.assertAlmostEqual(d.sol, -2.000005)
        self.assertEqual(d.tokens, {MINT: 1.0})

    def test_other_owners_and_failed_txs_ignored(self):
        tx = rpc_tx(WALLET, "sig", 1, post_tokens=[(MINT, 500, 0, OTHER)])
        self.assertEqual(delta_from_rpc_tx(tx, WALLET).tokens, {})
        self.assertIsNone(delta_from_rpc_tx(rpc_tx(WALLET, "s", 1, err={"x": 1}), WALLET))
        self.assertIsNone(delta_from_rpc_tx(None, WALLET))

    def test_json_encoding_with_lookup_table_keys(self):
        tx = rpc_tx(OTHER, "sig", 1)
        tx["transaction"]["message"]["accountKeys"] = [OTHER]          # plain "json" encoding
        tx["meta"]["loadedAddresses"] = {"writable": [WALLET], "readonly": []}
        tx["meta"]["preBalances"] = [SOL, 3 * SOL]
        tx["meta"]["postBalances"] = [SOL, 1 * SOL]
        self.assertAlmostEqual(delta_from_rpc_tx(tx, WALLET).sol, -2.0)


class HeliusDeltaTest(unittest.TestCase):
    def test_parsed_history_shape(self):
        tx = {"signature": "h1", "timestamp": 1_700_000_100, "slot": 9, "transactionError": None,
              "accountData": [
                  {"account": WALLET, "nativeBalanceChange": -1_500_005_000, "tokenBalanceChanges": []},
                  {"account": addr("ata"), "nativeBalanceChange": 0, "tokenBalanceChanges": [
                      {"userAccount": WALLET, "mint": MINT,
                       "rawTokenAmount": {"tokenAmount": "42000000", "decimals": 6}}]},
                  {"account": addr("pool"), "nativeBalanceChange": 1_500_000_000, "tokenBalanceChanges": [
                      {"userAccount": OTHER, "mint": MINT,
                       "rawTokenAmount": {"tokenAmount": "-42000000", "decimals": 6}}]},
              ]}
        d = delta_from_helius_tx(tx, WALLET)
        self.assertEqual((d.signature, d.ts, d.slot), ("h1", 1_700_000_100, 9))
        self.assertAlmostEqual(d.sol, -1.500005)
        self.assertEqual(d.tokens, {MINT: 42.0})
        self.assertIsNone(delta_from_helius_tx({**tx, "transactionError": {"e": 1}}, WALLET))


class FakeRpc(SolanaRpc):
    def __init__(self, sig_pages, txs):
        super().__init__("http://fake.local", rps=1000)
        self.sig_pages, self.txs, self.calls = list(sig_pages), txs, []

    def call(self, method, params, retries=0):
        self.calls.append((method, params))
        if method == "getSignaturesForAddress":
            return self.sig_pages.pop(0) if self.sig_pages else []
        return self.txs.get(params[0])


class FetchHistoryTest(unittest.TestCase):
    def test_skips_failed_and_reads_transactions(self):
        sigs = [{"signature": "a", "err": None}, {"signature": "b", "err": {"x": 1}}]
        rpc = FakeRpc([sigs], {"a": rpc_tx(WALLET, "a", 5, post_tokens=[(MINT, 10, 0)])})
        hist = fetch_history(WALLET, rpc, log=lambda *_: None)
        self.assertIsInstance(hist, History)
        self.assertTrue(hist.complete)
        self.assertEqual(hist.tx_count, 2)
        self.assertEqual([d.signature for d in hist.deltas], ["a"])

    def test_too_many_transactions_is_incomplete_and_cheap(self):
        page = [{"signature": f"s{i}", "err": None} for i in range(1000)]
        rpc = FakeRpc([page, page], {})
        hist = fetch_history(WALLET, rpc, max_txs=1500, log=lambda *_: None)
        self.assertFalse(hist.complete)
        self.assertFalse(any(m == "getTransaction" for m, _ in rpc.calls))


if __name__ == "__main__":
    unittest.main()
