window.GEM_WALLETS = {
 "generated_at": 1794399808,
 "provider": "rpc",
 "criteria": {
  "entry_min_usd": 100.0,
  "entry_max_usd": 500.0,
  "gem_profit_usd": 100000.0,
  "min_gems": 0,
  "min_multiple": 5.0,
  "min_trades": 5,
  "verified_only": true,
  "grace_hours": 72.0,
  "count_unrealized": false,
  "all_entries_in_range": false,
  "max_tokens": 300
 },
 "sources": {
  "seeds": {
   "ok": true,
   "wallets": 0
  },
  "pump-board": {
   "ok": false,
   "error": "HTTP 403 for https://frontend-api-v3.pump.fun/pnl-leaderboard?period=daily&limit=20: <!DOCTYPE html><html lang=\"en-US\"><head><title>Just a moment...</title><meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\"><meta http-equiv=\"X-UA"
  },
  "kolscan": {
   "ok": true,
   "wallets": 10
  },
  "fomo-top50": {
   "ok": true,
   "wallets": 96
  },
  "fomo": {
   "ok": false,
   "error": "FOMOAPI_KEY not set (Fomo's leaderboard is only inside the app; fomoapi.io is an unofficial API for it). Or paste Fomo wallets into wallets/seeds.txt"
  },
  "st-kols": {
   "ok": false,
   "error": "SOLANATRACKER_API_KEY not set"
  },
  "st-top": {
   "ok": false,
   "error": "SOLANATRACKER_API_KEY not set"
  },
  "gmgn": {
   "ok": false,
   "error": "GMGN_API_KEY not set (create one at gmgn.ai/ai)"
  },
  "verified-early": {
   "ok": true,
   "wallets": 19,
   "coins": 30
  },
  "pump-gems": {
   "ok": false,
   "error": "gem search needs SOLANATRACKER_API_KEY or GMGN_API_KEY (to see who made money on each coin)"
  }
 },
 "counts": {
  "scanned": 125,
  "strict": 0,
  "gem_hunter": 1,
  "rejected": 20,
  "error": 104
 },
 "wallets": [
  {
   "wallet": "9YmQh3JniNwU4DyreS1cZDYXczS3t1cari7Eg2qePLqe",
   "tier": "GEM_HUNTER",
   "labels": [
    "early buyer on 2 big coins: GATO early $50, MASK early $89"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 629,
    "judged": 629,
    "open": 0,
    "gems": 6,
    "wins_min_multiple": 15,
    "losses": 426,
    "min_multiple": 0.0,
    "median_multiple": 0.61,
    "best_multiple": 22.39,
    "invested_usd": 43616.01,
    "realized_usd": 6217.26,
    "gem_profit_usd": 5156.77,
    "hit_rate": 0.01,
    "unverified": 621,
    "tx_count": 2517
   },
   "reasons": [
    "traded 629 coins (> 300): bot / scalper",
    "614 trade(s) under 5x (worst 0.00x)",
    "621 trade(s) in coins Jupiter has not verified"
   ],
   "flags": [
    "1 gem(s) bought within 60s of launch: sniper / insider?",
    "9 weak trade(s) were coins sent to another wallet, so not necessarily real losses"
   ],
   "notes": [],
   "data_source": "helius",
   "gems": [
    {
     "mint": "HuAXPyDWDaMYFKuwQHpqL1oPnj93zdzWmtvFGzCeCUa7",
     "symbol": "MASK",
     "cost_usd": 88.53,
     "proceeds_usd": 1962.51,
     "value_usd": 0.0,
     "profit_usd": 1873.98,
     "multiple": 22.17,
     "buys": 1,
     "sells": 4,
     "first_buy_ts": 1790153609,
     "last_trade_ts": 1790212636,
     "launched_ts": 1790161463,
     "first_buy_sig": "3GGZwNaBvzWeqQARLtM9gBKMeMpKKCCUt6b5cCbPR2XCo6pE2MhRbfFf6UFXxFVUD5zyLx9PooZU8h8LzKaZ7zsb",
     "verified": true,
     "flags": []
    },
    {
     "mint": "5dvXTZ5qwgafnHtwu3Ls3QrWx1U4LQsFeCuJgkk4QEC6",
     "symbol": "EMBER",
     "cost_usd": 51.2,
     "proceeds_usd": 1146.54,
     "value_usd": 0.0,
     "profit_usd": 1095.34,
     "multiple": 22.39,
     "buys": 1,
     "sells": 8,
     "first_buy_ts": 1788992925,
     "last_trade_ts": 1789832655,
     "launched_ts": 1788992701,
     "first_buy_sig": "2peVkWHwb5uVnyeFP9mrESzBqZ2EDaYZYv7HdU31kUGu9zvVHwGUUmdcJocA5BDM1SZomSpYpSqacBKF3eVeX91i",
     "verified": true,
     "flags": []
    },
    {
     "mint": "98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump",
     "symbol": "PAID",
     "cost_usd": 49.24,
     "proceeds_usd": 862.64,
     "value_usd": 0.0,
     "profit_usd": 813.4,
     "multiple": 17.52,
     "buys": 1,
     "sells": 8,
     "first_buy_ts": 1789500154,
     "last_trade_ts": 1789511138,
     "launched_ts": 1789500144,
     "first_buy_sig": "31K8k6qRSYRVC3TkwbF1Qg8ydtQAkpqmF4foFMGCXJD8g2fkYf3P6ZiweVCXRrKrMNFqPaLrGZMRgrGtVa5hk3u7",
     "verified": true,
     "flags": []
    },
    {
     "mint": "HsprHxBRgiVaQdRf3TnKNuZZtaX9JUSPgMFdAkk6pump",
     "symbol": "GATO",
     "cost_usd": 98.9,
     "proceeds_usd": 822.55,
     "value_usd": 0.0,
     "profit_usd": 723.65,
     "multiple": 8.32,
     "buys": 2,
     "sells": 6,
     "first_buy_ts": 1787660802,
     "last_trade_ts": 1787781727,
     "launched_ts": 1787660841,
     "first_buy_sig": "cnRY9siSBVoJTQ1jUg6eqZfJBUvak8ndQDi2UDKeYPqKWEfHVYgRnbDkQGDMZPHTDCPhKR5smtWyNaHLXiUGNLe",
     "verified": true,
     "flags": []
    },
    {
     "mint": "8RVBk8vxLiUHueLUW1f4izFVqN3nWippLhkohKg6EGkS",
     "symbol": "KNOTS",
     "cost_usd": 39.59,
     "proceeds_usd": 412.25,
     "value_usd": 0.0,
     "profit_usd": 372.66,
     "multiple": 10.41,
     "buys": 1,
     "sells": 4,
     "first_buy_ts": 1788661063,
     "last_trade_ts": 1788735598,
     "launched_ts": 1788674285,
     "first_buy_sig": "4QL4bUWTy6j6yiumuYRMEBryWf1Hg4CeEYqvmTRqfvHPGmzCaXVYHbi6RhXCKXf3JVabdzL5Mrin8YUvte5Lm5rA",
     "verified": true,
     "flags": []
    },
    {
     "mint": "DD3AC2Cmr5rXzJ6ErRHeryx3ASLVMhSBALiUqeKcpump",
     "symbol": "Leafy",
     "cost_usd": 39.65,
     "proceeds_usd": 317.4,
     "value_usd": 0.0,
     "profit_usd": 277.75,
     "multiple": 8.01,
     "buys": 1,
     "sells": 4,
     "first_buy_ts": 1788038835,
     "last_trade_ts": 1788144649,
     "launched_ts": 1788039304,
     "first_buy_sig": "5PySCiWRNXTAAw5groBopRGFhooYi9Mik97GqnCMkQB7fLZebtmP9gXipGYSXyCGUbP41WGqVT5twftxwGEsbtep",
     "verified": true,
     "flags": []
    }
   ],
   "trades": [
    {
     "mint": "BCPk4HDTQdbaUS4qcGEgQnrwGQL6LSYp434uPfqepump",
     "symbol": "",
     "cost_usd": 60.55,
     "proceeds_usd": 27.11,
     "value_usd": 0.0,
     "profit_usd": -33.45,
     "multiple": 0.45,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790406803,
     "last_trade_ts": 1790411450,
     "launched_ts": null,
     "first_buy_sig": "MCENe2GrTtjLKYZyHFXY45Jh15G7hTa6JqYm9sonJsF3ZjbHqA5KY7cLqxJJM7s6kvkcK9CKEnvJEpoHG6AP6Bq",
     "verified": false,
     "flags": []
    },
    {
     "mint": "6G7taKgctMN3MP3uNnC1BfaX7b2QVvQWQw4bjvWw6kqP",
     "symbol": "",
     "cost_usd": 61.38,
     "proceeds_usd": 18.27,
     "value_usd": 0.0,
     "profit_usd": -43.12,
     "multiple": 0.3,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790385974,
     "last_trade_ts": 1790387474,
     "launched_ts": null,
     "first_buy_sig": "Xy7bV8WkmPCjcczs82CoR3bm8JtxyLKxnWBT1zVWqqGdMGKQ21YEYPoyvs9TCtFxAL9mU7a5JVXFHftAFRgiH51",
     "verified": false,
     "flags": []
    },
    {
     "mint": "Yd3BG57u53ieowSuqJCuvXmqt8KbmpsMjfFyuj4pump",
     "symbol": "",
     "cost_usd": 61.23,
     "proceeds_usd": 102.14,
     "value_usd": 0.0,
     "profit_usd": 40.92,
     "multiple": 1.67,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790382149,
     "last_trade_ts": 1790382227,
     "launched_ts": null,
     "first_buy_sig": "3CHFABfvvwsYyY7TMiNF3zxpHZY2QVUXmBzhTRs8YrG6RUSNWmApmUbDtCP8aqte4spyjBcYYgJcRNPwa815ma9x",
     "verified": false,
     "flags": []
    },
    {
     "mint": "HQpaEuLcwMnhMBKezYfVeZFXYMZJtGaLZTZaFvMWFMET",
     "symbol": "",
     "cost_usd": 61.09,
     "proceeds_usd": 63.62,
     "value_usd": 0.0,
     "profit_usd": 2.53,
     "multiple": 1.04,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790374021,
     "last_trade_ts": 1790411449,
     "launched_ts": null,
     "first_buy_sig": "4a8tQyvGvbCmcxbjXjeK7p5STbbe9xysRqsPXAPviPoUJS4Mx2JaD5rtbPNnbTxPuenBn2iNZ3y5ehtYN6qToYvV",
     "verified": false,
     "flags": []
    },
    {
     "mint": "CaxneAGGNABp1YFC5ziAYYBSyBYa5hErW5D1EXLKpump",
     "symbol": "",
     "cost_usd": 60.96,
     "proceeds_usd": 23.64,
     "value_usd": 0.0,
     "profit_usd": -37.32,
     "multiple": 0.39,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790373177,
     "last_trade_ts": 1790408120,
     "launched_ts": null,
     "first_buy_sig": "bwPCpw7SzusQcomFeyrkhYNhwmojuLDopnBDzNj4uG6ZF5Q84M73cuEZaM1uMFgX1SrFEYEVw832xMTAornezu1",
     "verified": false,
     "flags": []
    },
    {
     "mint": "HFzBj1HR6qH4JdSwntAjMfmAmxk93U2PQwQN9Wmdpump",
     "symbol": "",
     "cost_usd": 61.27,
     "proceeds_usd": 52.41,
     "value_usd": 0.0,
     "profit_usd": -8.87,
     "multiple": 0.86,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790364151,
     "last_trade_ts": 1790366698,
     "launched_ts": null,
     "first_buy_sig": "34MngZFmQzwc1QzSdMebvgzFsPHjph8YvruDNVv9h7kHD2dWEZRXiSjEU3eYyF8aUts83q8vt5hdYmpFsEnepYH4",
     "verified": false,
     "flags": []
    },
    {
     "mint": "A5hfZtxBwScohYzsFNuQtTSZ7qi54VNPhZrds2CMpump",
     "symbol": "",
     "cost_usd": 61.05,
     "proceeds_usd": 30.11,
     "value_usd": 0.0,
     "profit_usd": -30.93,
     "multiple": 0.49,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790361076,
     "last_trade_ts": 1790361680,
     "launched_ts": null,
     "first_buy_sig": "2Jv9NEUij8dTYSnnFLuZBmYtVJ4TxkMQBeeidhHNfFwgDkrqx8isfAQCfDz5DDVguFpXcaxufzGm3jEJ9BP6P3Mq",
     "verified": false,
     "flags": []
    },
    {
     "mint": "8Ftt6nNqchoKfQDMtj3U6iwETQCVGAK6gRQLx3PApump",
     "symbol": "",
     "cost_usd": 61.05,
     "proceeds_usd": 33.57,
     "value_usd": 0.0,
     "profit_usd": -27.48,
     "multiple": 0.55,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790360216,
     "last_trade_ts": 1790361623,
     "launched_ts": null,
     "first_buy_sig": "29VVBAAdq5t9HbcxWA2vmNPTe6ycC1GY9VizJx4NGhgXQSFvDfgwfeSKdTNUyxuHYVFa5RzJMGbLR5BQrBn3PoNR",
     "verified": false,
     "flags": []
    },
    {
     "mint": "7HMympkT3ZgPpEYaQbHssCNQ1zqD8gsVN1isuSGAikRt",
     "symbol": "",
     "cost_usd": 60.78,
     "proceeds_usd": 27.66,
     "value_usd": 0.0,
     "profit_usd": -33.12,
     "multiple": 0.46,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790357343,
     "last_trade_ts": 1790411437,
     "launched_ts": null,
     "first_buy_sig": "nmiywYtWHBHZ3Ri2ymU5acjdqgvmpWwE9Nw2m8ZC7EDYZeBwgcHwSbsoH32VsTH3hKYky6hpzmZgKGGKVPoA3jx",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9ef8bbV2d7kRmCfazikYjDynznesV34DhZoTHnawpump",
     "symbol": "",
     "cost_usd": 60.36,
     "proceeds_usd": 7.74,
     "value_usd": 0.0,
     "profit_usd": -52.62,
     "multiple": 0.13,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790342530,
     "last_trade_ts": 1790342538,
     "launched_ts": null,
     "first_buy_sig": "25cNqvm6xUAL5bmSS8xaoWEutu8vX3MHqJTyGDghD3FsZyWRZLQoHTgS22u1bTcVseJmgSHi3mD19Kan5RugQ9LK",
     "verified": false,
     "flags": []
    },
    {
     "mint": "CMMtMtYqsELs4PNvGRM76eVuKFEsDCXzUNQuLEH97ebL",
     "symbol": "wCat",
     "cost_usd": 118.14,
     "proceeds_usd": 177.27,
     "value_usd": 0.0,
     "profit_usd": 59.13,
     "multiple": 1.5,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790328864,
     "last_trade_ts": 1790411439,
     "launched_ts": 1789693307,
     "first_buy_sig": "5xpxYRmXurv5zp1rqmZvo6MQe8iXGaJSMAFv2vt3dkxLY9cPK3cQxHYZG9yocEDCr25AxUzm8CVpAF41keRHzqMM",
     "verified": false,
     "flags": []
    },
    {
     "mint": "AotFYJVM4hFQS97MWq6c2KoDgDYWFDCxLF9i8ZCfABPt",
     "symbol": "",
     "cost_usd": 174.73,
     "proceeds_usd": 107.1,
     "value_usd": 0.0,
     "profit_usd": -67.63,
     "multiple": 0.61,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790322608,
     "last_trade_ts": 1790411487,
     "launched_ts": null,
     "first_buy_sig": "2mfqvS3oHowioH7AokszN2aopKdGMAY1McaFTixsHFLTNMr7aTfpfXpWBUHBiY18n3duPtXwp8YYx4kdeivd2pUC",
     "verified": false,
     "flags": []
    },
    {
     "mint": "F1JnncwQzrT8BM9DNkU9uqU4qqiH11GbhRWqCTeHpump",
     "symbol": "",
     "cost_usd": 116.59,
     "proceeds_usd": 108.08,
     "value_usd": 0.0,
     "profit_usd": -8.51,
     "multiple": 0.93,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790322481,
     "last_trade_ts": 1790411484,
     "launched_ts": null,
     "first_buy_sig": "3VsF6Tc3qwnjuu8TnAcyTvAqD7sakVX6RpGYyxEtuz1WyARtMUf2r9i5yhbUtjbonvqTQAFrinRaFLPUnKyUkvms",
     "verified": false,
     "flags": []
    },
    {
     "mint": "C4N8LVsQ7q4TTbggFsZbtD9fihk6UpuMEXFuiaUVpump",
     "symbol": "",
     "cost_usd": 58.61,
     "proceeds_usd": 34.14,
     "value_usd": 0.0,
     "profit_usd": -24.47,
     "multiple": 0.58,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790309860,
     "last_trade_ts": 1790361756,
     "launched_ts": null,
     "first_buy_sig": "4xG3c7yLb9BHpshwcn8AbSE1fnz35DkKawgR4xGhANG7A4bSb9FNqm5q2YvZW7k4xG9wUJAik4mRfpk44LLs3qb7",
     "verified": false,
     "flags": []
    },
    {
     "mint": "7wewNUmQtvroZfosF7bFtjD2hSQMQqXTU6dB2pVQpump",
     "symbol": "",
     "cost_usd": 58.92,
     "proceeds_usd": 21.59,
     "value_usd": 0.0,
     "profit_usd": -37.32,
     "multiple": 0.37,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790306508,
     "last_trade_ts": 1790307243,
     "launched_ts": null,
     "first_buy_sig": "5ZV8ZbbVoFoeFA5NMPUATMFKRZVLwWqtzgF8Sqt9X72Cszigvbcxqbx6G6ut1ybwVNoNQTNWgL6WeqC7v3j5zwzT",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9HCr8Y1MLvHLY8VMazHvPkBxCbdHigVCNzHFX8impump",
     "symbol": "",
     "cost_usd": 59.39,
     "proceeds_usd": 16.11,
     "value_usd": 0.0,
     "profit_usd": -43.28,
     "multiple": 0.27,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790301095,
     "last_trade_ts": 1790301833,
     "launched_ts": null,
     "first_buy_sig": "GxvLoTCumaEYQRmvAxgNb8tHzJnEwV94xoP3eLNEUxvqf69cKzaMqiRKPRamjFvS8yMpgo14Day3zeV1gXfrTXK",
     "verified": false,
     "flags": []
    },
    {
     "mint": "LN1BD66bzhThhh8fjKcWsSDZ6TLhXb6KTAE2uVS459U",
     "symbol": "",
     "cost_usd": 117.33,
     "proceeds_usd": 185.78,
     "value_usd": 0.0,
     "profit_usd": 68.45,
     "multiple": 1.58,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790281097,
     "last_trade_ts": 1790283577,
     "launched_ts": null,
     "first_buy_sig": "29Ya6oo9TdKERZ2GYyyGjbLr1yrVMqrp7iBwQvxMS6tCfESYcK6xGuwgmfFX7C2zMT9Li8vgtAKnsoyu7zRJmrqJ",
     "verified": false,
     "flags": []
    },
    {
     "mint": "H4WmjgmbHdpfzFxhEWfevdZ3agMhZPKHjKVuGWpFrTT4",
     "symbol": "",
     "cost_usd": 58.83,
     "proceeds_usd": 18.03,
     "value_usd": 0.0,
     "profit_usd": -40.8,
     "multiple": 0.31,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790274464,
     "last_trade_ts": 1790340668,
     "launched_ts": null,
     "first_buy_sig": "3FgCBkmbyAHHwuLAmtMySKbLPzUpbhUuq8g7XwZ7ZhTVLciZPuVznmtUfwcnvJMACvLgAC3xj91Lo473Fi7hQfxV",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9bM3eaUZqHDmmZhDRn3WP16PAwWKjuEwWfer4cW8pump",
     "symbol": "",
     "cost_usd": 58.83,
     "proceeds_usd": 29.46,
     "value_usd": 0.0,
     "profit_usd": -29.37,
     "multiple": 0.5,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790274183,
     "last_trade_ts": 1790361999,
     "launched_ts": null,
     "first_buy_sig": "5Fpr8HdYu6fCMWyGVPyvVdxPbTvAUr2im4ttvmvWJq4RxScR7EoSbykusPfkrYTPnWeFeCXCgNsSQqazheAJZZac",
     "verified": false,
     "flags": []
    },
    {
     "mint": "AcosZxVz1rYypcJFyvj1ewzm2J7pRuCUBpFx1iRoqT5h",
     "symbol": "",
     "cost_usd": 58.82,
     "proceeds_usd": 18.0,
     "value_usd": 0.0,
     "profit_usd": -40.82,
     "multiple": 0.31,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790274003,
     "last_trade_ts": 1790274123,
     "launched_ts": null,
     "first_buy_sig": "29tRkkxbknpbPxTHBQjkZT2tN69BpQZKN2rY3NHAFdyNr6VUx49wYMBhcqN2DttY66xijmmhMHzNRhYC6FSYXpKP",
     "verified": false,
     "flags": []
    },
    {
     "mint": "55mH366XFZzouoCry2qsHZ2E1JoU4Ema1zQ4bijXraS4",
     "symbol": "",
     "cost_usd": 58.75,
     "proceeds_usd": 75.42,
     "value_usd": 0.0,
     "profit_usd": 16.66,
     "multiple": 1.28,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790272230,
     "last_trade_ts": 1790349053,
     "launched_ts": null,
     "first_buy_sig": "SGhSXzCWqyBzWLBPkGaiiMYGdXMg4PRof4PjLxhveuzAWgXETXf2zizt2ZHmnWEtjWX1bDS7e5KhQHX1G8qRbLM",
     "verified": false,
     "flags": []
    },
    {
     "mint": "4rwePMUQobtTHu7SuPsYtHKLLU1bp6Ckehtrscfqpump",
     "symbol": "",
     "cost_usd": 59.01,
     "proceeds_usd": 16.47,
     "value_usd": 0.0,
     "profit_usd": -42.54,
     "multiple": 0.28,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790267826,
     "last_trade_ts": 1790301954,
     "launched_ts": null,
     "first_buy_sig": "2rRRZigPwDFqtXyZYTTQbdhjKdBsGz9fYQ5A9QBz8wHeGv87ENgv4pGi679cGBs2wChvShipSDpgwuA4cQkm7fXN",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9w5r7KgsUXqwbztnL3yCMCdp28yrN3EYv3xzsZFVpump",
     "symbol": "",
     "cost_usd": 58.01,
     "proceeds_usd": 85.38,
     "value_usd": 0.0,
     "profit_usd": 27.37,
     "multiple": 1.47,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790265364,
     "last_trade_ts": 1790265524,
     "launched_ts": null,
     "first_buy_sig": "5QGGhvTT8z5HGwQiypCcPntCxhVFLM4a5V8rfPkvAib9voiaCUMcq9JutVBdAfUoDkJg5wZaZ2X9amdG4SnoKtrq",
     "verified": false,
     "flags": []
    },
    {
     "mint": "HS7dp8vQdKqQeYLoweBYtpKAUFLXY3pcjMLktJGcpump",
     "symbol": "",
     "cost_usd": 58.01,
     "proceeds_usd": 31.64,
     "value_usd": 0.0,
     "profit_usd": -26.38,
     "multiple": 0.55,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790263873,
     "last_trade_ts": 1790265475,
     "launched_ts": null,
     "first_buy_sig": "52ER1mr1cg8NtP5uxEVpgTZjUF934YpfBpspMoyY31CH4AA64fztNbBRUKQwkpZe2bQvMovqcbgW2zyqU1VPGre7",
     "verified": false,
     "flags": []
    },
    {
     "mint": "C4JhvvsdsmUGqdQrvkEegYCh7UsCdAM3JjEfDQCApump",
     "symbol": "",
     "cost_usd": 57.68,
     "proceeds_usd": 32.15,
     "value_usd": 0.0,
     "profit_usd": -25.53,
     "multiple": 0.56,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790261679,
     "last_trade_ts": 1790265483,
     "launched_ts": null,
     "first_buy_sig": "4dpMV4F88mVzVEkdXo5MiyvutQsWhjHSDDM1f3cdjnMjhoB3TkQSJ9vF9T17ZLZXTz1Ds1Kx8EddSrSkXdMfBG3E",
     "verified": false,
     "flags": []
    },
    {
     "mint": "43LzcTwCAPs6wiY8bMbnFWv9nAk4WxxFDE9DQskJpump",
     "symbol": "",
     "cost_usd": 57.68,
     "proceeds_usd": 30.37,
     "value_usd": 0.0,
     "profit_usd": -27.31,
     "multiple": 0.53,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790259413,
     "last_trade_ts": 1790265490,
     "launched_ts": null,
     "first_buy_sig": "4kdSKPwx4t6a3UpSEbvZCyGuteUKEAbSuCxyGbsqesN39PngeKAjDZSc16weTojXhtKyBisH6fp7uU2873XJpNeE",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9d1Th8ppx517L3i5mYiyaxVr57zk1bbHywWzTzQWpump",
     "symbol": "",
     "cost_usd": 57.49,
     "proceeds_usd": 30.89,
     "value_usd": 0.0,
     "profit_usd": -26.59,
     "multiple": 0.54,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790257441,
     "last_trade_ts": 1790265495,
     "launched_ts": null,
     "first_buy_sig": "5T3C56BYP98HFK6ZCnzyTwPEFv1KXmeTMQcHGyADjx2ZhfaTFoGHngGt2CAfbv7m1JEPUTgUYLCLVHBMpGpW71fD",
     "verified": false,
     "flags": []
    },
    {
     "mint": "6KvaPiwiWgWmwQBgxtH7KAV3ZmRUjFGMEGx4fY3EeiJ3",
     "symbol": "",
     "cost_usd": 57.08,
     "proceeds_usd": 48.78,
     "value_usd": 0.0,
     "profit_usd": -8.3,
     "multiple": 0.85,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790253684,
     "last_trade_ts": 1790265501,
     "launched_ts": null,
     "first_buy_sig": "4rQqVwF2q5tB4st1NU5Y55HzcvXFTDmhCQ2KvFTSm2EBhj7jxD4AsTSYEJYDFMfWSvBz5w1TphEAZise3RWdRnt1",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9jhbFbyVao7eNVRtgFn5iZdJxmsWEJDyWkEcBvzpump",
     "symbol": "",
     "cost_usd": 56.91,
     "proceeds_usd": 23.82,
     "value_usd": 0.0,
     "profit_usd": -33.09,
     "multiple": 0.42,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790245822,
     "last_trade_ts": 1790249088,
     "launched_ts": null,
     "first_buy_sig": "38Sz2DoWzMYGzPUNnrDNA3553vXrg3EEHrXZkn3LUjxqKtyuSnPMJumiaUMAjoCAb4sjdoNStseyqQQu2kgg9qkv",
     "verified": false,
     "flags": []
    },
    {
     "mint": "5MiQQdXkyc8fqp6Yco7oUZKBRhFRyx7A2CqTfhfEpump",
     "symbol": "",
     "cost_usd": 57.11,
     "proceeds_usd": 33.51,
     "value_usd": 0.0,
     "profit_usd": -23.6,
     "multiple": 0.59,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790240601,
     "last_trade_ts": 1790249082,
     "launched_ts": null,
     "first_buy_sig": "2sNgdaHJyfbzANbVvN8SMypiXChD4EirVGMTqZodFzWforMD41EhzBfDtyrJCRWhvzbcxDWzsfWPt9jtM54BmqgH",
     "verified": false,
     "flags": []
    },
    {
     "mint": "334U95VK1Ygwijrrwgq1Bde321YgZ4NcqMpabgm1oiHx",
     "symbol": "",
     "cost_usd": 172.77,
     "proceeds_usd": 420.41,
     "value_usd": 0.0,
     "profit_usd": 247.64,
     "multiple": 2.43,
     "buys": 1,
     "sells": 4,
     "first_buy_ts": 1790222109,
     "last_trade_ts": 1790411492,
     "launched_ts": null,
     "first_buy_sig": "3Vx61njPTjoranUmUTDtzibXX6BCrW4FCAHYD8geN5yNuJLqQiXF97EqbksPUQTzjE4p3N6SD71dQ1DaSujNNorQ",
     "verified": false,
     "flags": []
    },
    {
     "mint": "h35vn1cWSuEztxLA3Gkasnoaeay5DBNzvSkaaj3pump",
     "symbol": "",
     "cost_usd": 57.79,
     "proceeds_usd": 10.37,
     "value_usd": 0.0,
     "profit_usd": -47.42,
     "multiple": 0.18,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790221068,
     "last_trade_ts": 1790264050,
     "launched_ts": null,
     "first_buy_sig": "2hsei7qrhihLXpMpKmtAcbgy9NhN4CJvNtMkmHeYZs7JKStHrGUqrhRNAWQUN4Nud8HFz4HtrucuoGY3uBbaYr33",
     "verified": false,
     "flags": []
    },
    {
     "mint": "GUVCzeXi8W911GaJxVkTncV825MwrMhPpL79oSuLpump",
     "symbol": "",
     "cost_usd": 57.83,
     "proceeds_usd": 29.02,
     "value_usd": 0.0,
     "profit_usd": -28.81,
     "multiple": 0.5,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790205969,
     "last_trade_ts": 1790224554,
     "launched_ts": null,
     "first_buy_sig": "3z8zFcWwxwT1hXqQFSFLQoxeZxY1SPvVMQ6foVSiV1NFrD3siTJgtLT57YSDkPmTyKjKZS51dDmRqz5V1Q28zNVC",
     "verified": false,
     "flags": []
    },
    {
     "mint": "Anx4cKYhXrtMzxVb2QJo1Wi2te1RKodpAzN5p3DsSTNK",
     "symbol": "",
     "cost_usd": 57.76,
     "proceeds_usd": 109.66,
     "value_usd": 0.0,
     "profit_usd": 51.91,
     "multiple": 1.9,
     "buys": 1,
     "sells": 3,
     "first_buy_ts": 1790201721,
     "last_trade_ts": 1790411490,
     "launched_ts": null,
     "first_buy_sig": "2zTXWWysqs5ezVoxw4qKCXWrGLtedvxqyLL2HhoA3e65vMu3LLKQNHPnUEiDCvhd5wtNWGiVY3hiPUusBMXnsdt5",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9yyxC9AtYxuijVrVfZjoYY2m3fRDuyYYF1VmKzRp9joC",
     "symbol": "",
     "cost_usd": 57.42,
     "proceeds_usd": 14.45,
     "value_usd": 0.0,
     "profit_usd": -42.97,
     "multiple": 0.25,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790196839,
     "last_trade_ts": 1790197015,
     "launched_ts": null,
     "first_buy_sig": "HNAMmtyckUqJ8ni9mVsUMv1SEAjHkj29ySXhqQX3GsGYbQgGRGVuoxhghGswTevWYaWpkXytkR9Tz2ngvvgWtcV",
     "verified": false,
     "flags": []
    },
    {
     "mint": "CLZ92xqMSaKtp1rrtduH84VkUk6cYjSi623gGZQZpump",
     "symbol": "",
     "cost_usd": 57.49,
     "proceeds_usd": 17.53,
     "value_usd": 0.0,
     "profit_usd": -39.96,
     "multiple": 0.3,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790190084,
     "last_trade_ts": 1790190431,
     "launched_ts": null,
     "first_buy_sig": "F1HUExxci4jgtVSEKKT6GzdX6dCNUWzayQmo7iwE4tYHRR41zVAoh5fZLsJbNVU8pRNbacQ7hqSv5F9K1K26hde",
     "verified": false,
     "flags": []
    },
    {
     "mint": "7VqKEWmPdTsMkFS3QxraDhdjrFbJ8btEmNB9HvXjpump",
     "symbol": "",
     "cost_usd": 57.51,
     "proceeds_usd": 28.81,
     "value_usd": 0.0,
     "profit_usd": -28.7,
     "multiple": 0.5,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790188405,
     "last_trade_ts": 1790224563,
     "launched_ts": null,
     "first_buy_sig": "4Zk7NQYA2obqgtL3xf48eLKYGQhkHTYzfno3ZXqe4YwoBcF3aaay7u9427Rntj9SMyrQrwLyecExhtA68JtcwpYd",
     "verified": false,
     "flags": []
    },
    {
     "mint": "JB7kpVap8MUguKVNv3Zpq1DJQnpzvaycCo4sSGrJevzu",
     "symbol": "",
     "cost_usd": 57.36,
     "proceeds_usd": 23.15,
     "value_usd": 0.0,
     "profit_usd": -34.21,
     "multiple": 0.4,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790181039,
     "last_trade_ts": 1790183094,
     "launched_ts": null,
     "first_buy_sig": "3voV93BHMyuKeeudKnb1NMjTqpU4isJ1stMFdG2g3QuTSLTLxBfiyMzgVd3rCpiJdz73rn4ZkDUczK8mXriKuN9V",
     "verified": false,
     "flags": []
    },
    {
     "mint": "8gfTLThNUXpdvXvcZ8BpM76mHPo7AKBQA8CH5V6Lpump",
     "symbol": "",
     "cost_usd": 88.42,
     "proceeds_usd": 25.52,
     "value_usd": 0.0,
     "profit_usd": -62.9,
     "multiple": 0.29,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790159812,
     "last_trade_ts": 1790159935,
     "launched_ts": null,
     "first_buy_sig": "Hp7zsHnM2MVqtNeWq25B8xgmkJ5LwbMvGRLcx2exz3bQaLjdxTJm9WjNeAsRAFDpS5sdSgUpE8vFmQcAzVEsPTn",
     "verified": false,
     "flags": []
    },
    {
     "mint": "4ExxkBpoMe52JqPT2U8gEcUx8UJ2RKGXQRFBzXG5Nsbm",
     "symbol": "",
     "cost_usd": 59.0,
     "proceeds_usd": 51.69,
     "value_usd": 0.0,
     "profit_usd": -7.3,
     "multiple": 0.88,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790156878,
     "last_trade_ts": 1790159900,
     "launched_ts": null,
     "first_buy_sig": "574HKnBw6sAi9RZsb1Do5wjtKWGoDQVWqD2VKiHyorUJBy1eVfBiKDvvAe8Fxb9fTsP37RhPM8st2eEHvBQSPx4w",
     "verified": false,
     "flags": []
    },
    {
     "mint": "BqvDcHLN7jmUqrSV2VEUzthia4tCDEK6dXbfZ7qppump",
     "symbol": "",
     "cost_usd": 59.0,
     "proceeds_usd": 25.75,
     "value_usd": 0.0,
     "profit_usd": -33.24,
     "multiple": 0.44,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790155984,
     "last_trade_ts": 1790183104,
     "launched_ts": null,
     "first_buy_sig": "5iBvMncQDynti7DArtHTrfFNiBwrKRwi83bXQgirCd17MwFVznHawVoc6Vv1gETLruFhcpVvfs5SRaCQcWxJY6Kz",
     "verified": false,
     "flags": []
    },
    {
     "mint": "HuAXPyDWDaMYFKuwQHpqL1oPnj93zdzWmtvFGzCeCUa7",
     "symbol": "MASK",
     "cost_usd": 88.53,
     "proceeds_usd": 1962.51,
     "value_usd": 0.0,
     "profit_usd": 1873.98,
     "multiple": 22.17,
     "buys": 1,
     "sells": 4,
     "first_buy_ts": 1790153609,
     "last_trade_ts": 1790212636,
     "launched_ts": 1790161463,
     "first_buy_sig": "3GGZwNaBvzWeqQARLtM9gBKMeMpKKCCUt6b5cCbPR2XCo6pE2MhRbfFf6UFXxFVUD5zyLx9PooZU8h8LzKaZ7zsb",
     "verified": true,
     "flags": []
    },
    {
     "mint": "C4AZWiWeZ51VfgC6UoBaWDHaxc42vkkZEgfWEMzmpump",
     "symbol": "",
     "cost_usd": 59.14,
     "proceeds_usd": 32.47,
     "value_usd": 0.0,
     "profit_usd": -26.67,
     "multiple": 0.55,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790152251,
     "last_trade_ts": 1790152493,
     "launched_ts": null,
     "first_buy_sig": "2xP4vgCfahzDdBYXQk2fmMgujvzppRYpjdaovWZqzXNPaTw2kpF1vjUMZanxcNXAL5QfUMXbBSvkXcNaGiCnNgX7",
     "verified": false,
     "flags": []
    },
    {
     "mint": "BZNrBf2jQyzFgYevQX9RvEDQMeoe5FmTZwTuXkpZwTQe",
     "symbol": "",
     "cost_usd": 89.11,
     "proceeds_usd": 26.52,
     "value_usd": 0.0,
     "profit_usd": -62.59,
     "multiple": 0.3,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790150346,
     "last_trade_ts": 1790152705,
     "launched_ts": null,
     "first_buy_sig": "3pZ16dJVY21o4Uu5gj9w9hg4rw1oDTgdcpAKRWMUPyFL2nA19WC2R3qc6AShpEud9qqnLXVyBazhzvYzsfoweTE8",
     "verified": false,
     "flags": []
    },
    {
     "mint": "12YqzTEzpLvjwDVAezog2WWQFoMSroBeXWLqodY1pump",
     "symbol": "",
     "cost_usd": 59.51,
     "proceeds_usd": 60.2,
     "value_usd": 0.0,
     "profit_usd": 0.69,
     "multiple": 1.01,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790148608,
     "last_trade_ts": 1790149578,
     "launched_ts": null,
     "first_buy_sig": "fSG74pYc7pNzLSAqbXiZZDLGfvHCPEnZNiFSXC7t7i5CV9zPLh1KgS9PaBQ2MMFKMDo1PjtZti3cWnQRMgusAdr",
     "verified": false,
     "flags": []
    },
    {
     "mint": "h4mTQoh5BvdNWvYE3s4Axn8hvxQdRwSypoPY2jkpump",
     "symbol": "",
     "cost_usd": 59.7,
     "proceeds_usd": 20.6,
     "value_usd": 0.0,
     "profit_usd": -39.09,
     "multiple": 0.35,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790135891,
     "last_trade_ts": 1790135922,
     "launched_ts": null,
     "first_buy_sig": "5LNMXVcTxSwsDrqBswGR7eB7Lqe8PLgAmVsCqAu45s8L7Y2BM1HifkxDieZCGdiB2WWxt3ph9Ji5jQ6nCRiTJytw",
     "verified": false,
     "flags": []
    },
    {
     "mint": "CbYhZxd3twHAs7Ff5Ztuijrim7F1iLY2Zz9j7CBupump",
     "symbol": "",
     "cost_usd": 59.89,
     "proceeds_usd": 28.02,
     "value_usd": 0.0,
     "profit_usd": -31.86,
     "multiple": 0.47,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790135751,
     "last_trade_ts": 1790149585,
     "launched_ts": null,
     "first_buy_sig": "5K7LSRd3RHSF2SLXSNPF3EBmHqMT4npMTFULYBA2RFz77fo25nNdgWEzMioX3c1WHZZ4UuyBe9KTYb2q4xUw4dcQ",
     "verified": false,
     "flags": []
    },
    {
     "mint": "cKKLp76WywbAwr2WpuMENcoctoV3WvNjmpDBzvYpump",
     "symbol": "",
     "cost_usd": 59.71,
     "proceeds_usd": 8.73,
     "value_usd": 0.0,
     "profit_usd": -50.98,
     "multiple": 0.15,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790135401,
     "last_trade_ts": 1790178513,
     "launched_ts": null,
     "first_buy_sig": "3AmqCkA2t6AC91kAwmeHEqXM2rCYEVTwguohfXdAkDC921x1CvfTRAqNbdSBAxqwBq3672hJD8wYvR3923XyUenm",
     "verified": false,
     "flags": []
    },
    {
     "mint": "6JRizm9nmwSyRfYSwQrgTe8rK66aMKMCkCM8K7ngFszD",
     "symbol": "",
     "cost_usd": 59.62,
     "proceeds_usd": 20.15,
     "value_usd": 0.0,
     "profit_usd": -39.47,
     "multiple": 0.34,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790116902,
     "last_trade_ts": 1790117880,
     "launched_ts": null,
     "first_buy_sig": "4uDov4X5TttjtT3AoPqD9cZFzP85YVmxrzpGZ7roUSgrrSRYyeE62wQSYxZ7u2NgeJkhoUv2YjNsD5suNJgoWib2",
     "verified": false,
     "flags": []
    },
    {
     "mint": "81eLTC5n4xMyGae5iDe6Vsb7kYPyrGEauASvBWfhpump",
     "symbol": "",
     "cost_usd": 59.45,
     "proceeds_usd": 21.19,
     "value_usd": 0.0,
     "profit_usd": -38.26,
     "multiple": 0.36,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790114644,
     "last_trade_ts": 1790122996,
     "launched_ts": null,
     "first_buy_sig": "3TeFxbEo2eKmVKort2LDfS1PX6yT8tUy4LHdebSQ8oNGAJuYbGV3TEdoti4oTwvDXY1dsx7jeR5nRM13pDixZwSr",
     "verified": false,
     "flags": []
    },
    {
     "mint": "GwQdjb2NcmFw8nqVQKp9XV89e7kuFWgLLfbJM6eRpump",
     "symbol": "",
     "cost_usd": 59.38,
     "proceeds_usd": 24.26,
     "value_usd": 0.0,
     "profit_usd": -35.13,
     "multiple": 0.41,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790109138,
     "last_trade_ts": 1790123051,
     "launched_ts": null,
     "first_buy_sig": "5b4rWQoVCVYwAqpV48Y21N3HXegpJQtv68pRR28AhPLVPbH79ggsEQ9APHK8Uz8pyenX7xkGwuty5PqurFFfsANJ",
     "verified": false,
     "flags": []
    },
    {
     "mint": "3i7NgvNqmeKsL7o2ggyAktdJjgxthfbMbYnCJiH6fZY9",
     "symbol": "",
     "cost_usd": 59.51,
     "proceeds_usd": 13.35,
     "value_usd": 0.0,
     "profit_usd": -46.15,
     "multiple": 0.22,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790103080,
     "last_trade_ts": 1790123061,
     "launched_ts": null,
     "first_buy_sig": "6pacphUVpHWZRMjyasJ8BzNF4fvRLTXYjV8EdcMd2NgWr4HPQEq1nXdwfB4VfEr7eMFpaTKBoGKhDcWKhzKEPPe",
     "verified": false,
     "flags": []
    },
    {
     "mint": "FTp5HYt7FcpHX9pPh9DmVcH6rMyUKTDj4owF8Q79wygx",
     "symbol": "",
     "cost_usd": 59.17,
     "proceeds_usd": 28.93,
     "value_usd": 0.0,
     "profit_usd": -30.24,
     "multiple": 0.49,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790099625,
     "last_trade_ts": 1790123008,
     "launched_ts": null,
     "first_buy_sig": "1WDgyXJT73cJXqkc2yBGetEZ9P9V3mWme3hgaFoEhS3vAqNUbu9hqmmhCK8nsN4FNRSCNVgNZYTWqjinDFaLEue",
     "verified": false,
     "flags": []
    },
    {
     "mint": "AbGE23ZYi5S2vRuo6t4Nyz9fqd83jyEojHrepVWCpump",
     "symbol": "",
     "cost_usd": 88.6,
     "proceeds_usd": 118.89,
     "value_usd": 0.0,
     "profit_usd": 30.29,
     "multiple": 1.34,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790096647,
     "last_trade_ts": 1790101679,
     "launched_ts": null,
     "first_buy_sig": "5zUXXN3TmA869hhCxQwWZWZFWCo3gJshnUC1WcV32asAMjFTX56A7CkymG2S4TTWcRajPppM45yptqU2HgYSxusb",
     "verified": false,
     "flags": []
    },
    {
     "mint": "8GVQG7YifLZ9cesTjhfB8EUVMPvpWFhCMW2UYJ5mjw9t",
     "symbol": "",
     "cost_usd": 59.0,
     "proceeds_usd": 73.41,
     "value_usd": 0.0,
     "profit_usd": 14.41,
     "multiple": 1.24,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790096100,
     "last_trade_ts": 1790099273,
     "launched_ts": null,
     "first_buy_sig": "5HREJmSkUcJ4yPJ3Eg94c9EuTZEkwQ1eFfNBUUWs7iDV1AFJ2xfXgRwnTLwtwscnivfjDN5PvzcJADYe3qgyZvpJ",
     "verified": false,
     "flags": []
    },
    {
     "mint": "Gmj3RUzmomj2e2o84oHACmvv5nf7YfkjDntRtW1Zpump",
     "symbol": "",
     "cost_usd": 59.01,
     "proceeds_usd": 10.87,
     "value_usd": 0.0,
     "profit_usd": -48.15,
     "multiple": 0.18,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790095065,
     "last_trade_ts": 1790095133,
     "launched_ts": null,
     "first_buy_sig": "7vwZeui1FLqXHHz1durKgGSRHB9x2QWH6d6K6BKihccbccKHRp4YURSAcnCsuMnM8eMke6nTef3gGCoLC8LckHR",
     "verified": false,
     "flags": []
    },
    {
     "mint": "Pei2zjr4gvb7sPTYRMYbZXYzTE3826k28ehTXCg45EC",
     "symbol": "",
     "cost_usd": 59.0,
     "proceeds_usd": 23.35,
     "value_usd": 0.0,
     "profit_usd": -35.65,
     "multiple": 0.4,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790093192,
     "last_trade_ts": 1790094234,
     "launched_ts": null,
     "first_buy_sig": "5ePfjyvaHC17mTweodRaarEPHu7iwXJGU2ABivSZfYXXzoEFdALtpczgX1p6EbXgQJdT1SQ522GqSZEr9rRmHJEw",
     "verified": false,
     "flags": []
    },
    {
     "mint": "H9JwarQSuFk4q6ekuMpig4CkJyv7NtSRQ8BbCsmapump",
     "symbol": "GIGAINU",
     "cost_usd": 59.02,
     "proceeds_usd": 82.86,
     "value_usd": 0.0,
     "profit_usd": 23.83,
     "multiple": 1.4,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790088476,
     "last_trade_ts": 1790122995,
     "launched_ts": 1790110689,
     "first_buy_sig": "5SFAvhgf5dfxi4RTWfUpcVZiLWo7uxHJsWw8xnZntP3bxVksddE5jp6j4oEi32yJrAforcFvUqk4NoVSBShECh89",
     "verified": false,
     "flags": []
    },
    {
     "mint": "H6ibmg2HroqMWMFbTkzsuGsnRumuULFBL6hoMLmZmLe",
     "symbol": "",
     "cost_usd": 59.02,
     "proceeds_usd": 63.56,
     "value_usd": 0.0,
     "profit_usd": 4.54,
     "multiple": 1.08,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1790085726,
     "last_trade_ts": 1790086843,
     "launched_ts": null,
     "first_buy_sig": "3VvmczTxQGSkcpkz8rGAA9MUESdskkUZdARnLhYPkqvvK6dvK3Bcky8mGKG9xLCkrtHP9xp7VqbXi9CrzPWBCPZw",
     "verified": false,
     "flags": []
    },
    {
     "mint": "4Vt5NQFTXYuCVvmkbcSG5ScMoMVyHJRxMoYUyC4vpump",
     "symbol": "",
     "cost_usd": 58.62,
     "proceeds_usd": 2.36,
     "value_usd": 0.0,
     "profit_usd": -56.27,
     "multiple": 0.04,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1790058030,
     "last_trade_ts": 1790058178,
     "launched_ts": null,
     "first_buy_sig": "4rtKWBHwaohgC22NcKD1B2jddD2yVxrCKkNQyCXyMvZoiftQyQzJEaR1RKANkJ6v2xK4nCwMydENDPwukf5GJNzC",
     "verified": false,
     "flags": []
    }
   ]
  },
  {
   "wallet": "5V8jnw5Pp2b7f7SD1tkvxkNqfiDmZHvt8WRuLyVm59iL",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: ZCAT early $39, GATO early $69"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 319,
    "judged": 319,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 1,
    "losses": 200,
    "min_multiple": 0.0,
    "median_multiple": 0.94,
    "best_multiple": 6.97,
    "invested_usd": 43034.21,
    "realized_usd": 429.28,
    "gem_profit_usd": 0,
    "hit_rate": 0.0,
    "unverified": 312,
    "tx_count": 1612
   },
   "reasons": [
    "traded 319 coins (> 300): bot / scalper",
    "0 winning trade(s) (5x+ on verified coins); needs 5",
    "318 trade(s) under 5x (worst 0.00x)",
    "312 trade(s) in coins Jupiter has not verified"
   ],
   "flags": [
    "3 weak trade(s) were coins sent to another wallet, so not necessarily real losses"
   ],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": [
    {
     "mint": "EjRC7Lk6SRPXpdq3PZx6siNXs9ULd6J4Gbvzia6p4Yjj",
     "symbol": "",
     "cost_usd": 78.02,
     "proceeds_usd": 76.98,
     "value_usd": 0.0,
     "profit_usd": -1.04,
     "multiple": 0.99,
     "buys": 2,
     "sells": 1,
     "first_buy_ts": 1788252817,
     "last_trade_ts": 1788252933,
     "launched_ts": null,
     "first_buy_sig": "2n6QgX1EyKBh9ssFzJh25KSfAaSpTnicizRCAA8dRhYanGLwuYgER5WmXsMhGP49iBDxtMeopJXDaGedwq49d8Ta",
     "verified": false,
     "flags": []
    },
    {
     "mint": "4qAv1QAoFpNtTqxpZmyjLfxM3RRcLqT84gJf3KNrQS3c",
     "symbol": "",
     "cost_usd": 78.27,
     "proceeds_usd": 136.37,
     "value_usd": 0.0,
     "profit_usd": 58.1,
     "multiple": 1.74,
     "buys": 2,
     "sells": 3,
     "first_buy_ts": 1788226967,
     "last_trade_ts": 1788227108,
     "launched_ts": null,
     "first_buy_sig": "cibFiBnMk5MhVMzBEsC6oTwC1bYM9MtAWsX9JXSDy8P5WtCDMHTFnM1ooxhYzairru4EebAELZwJgjMN5uZjhNM",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9JSY2Zo8VM3dhdvbGgd7FqAWeQf8F39QsvkzKLpvpump",
     "symbol": "",
     "cost_usd": 317.76,
     "proceeds_usd": 178.56,
     "value_usd": 0.0,
     "profit_usd": -139.19,
     "multiple": 0.56,
     "buys": 5,
     "sells": 2,
     "first_buy_ts": 1788225303,
     "last_trade_ts": 1788226857,
     "launched_ts": null,
     "first_buy_sig": "2KkhDP7GN3SKLVdySMA9zYwn6C39k9bwikxgYxqfDnhU3TMLvmQVeBsgkCHJ661woYELFEbyRpdXzJaDSCbLVKeJ",
     "verified": false,
     "flags": []
    },
    {
     "mint": "59CsdLWQtyGJnTSyFBnKWfJtXTFwenGbZ7PQz1uwpump",
     "symbol": "",
     "cost_usd": 206.45,
     "proceeds_usd": 231.84,
     "value_usd": 0.0,
     "profit_usd": 25.39,
     "multiple": 1.12,
     "buys": 2,
     "sells": 1,
     "first_buy_ts": 1788223058,
     "last_trade_ts": 1788223937,
     "launched_ts": null,
     "first_buy_sig": "4f4FskJ7ybjuYAd1Xmq2eoVrxDQKunvndFqhv3ES3Ks2E5bJmW3UTLJ5xRUZXh2yTQbYHw7mZdSdqDQLXjQLFUNu",
     "verified": false,
     "flags": []
    },
    {
     "mint": "2j424TqiLdkWs7FZbjHDoDuVhgbHwaRAA9fENKgWpump",
     "symbol": "",
     "cost_usd": 55.92,
     "proceeds_usd": 38.38,
     "value_usd": 0.0,
     "profit_usd": -17.54,
     "multiple": 0.69,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788217517,
     "last_trade_ts": 1788217543,
     "launched_ts": null,
     "first_buy_sig": "5mEQf9XKtSFcu3sPXBZ1EomT8R1UxJSE48wNNA8pTJikmBhB6ecVn2pbFeotreRSxKKdPXW45mAQcaFWYdvPNQVf",
     "verified": false,
     "flags": []
    },
    {
     "mint": "Dy6NQNYMcjN8zDcYp16eTuUbdiJr6w55HYJQwXwqpump",
     "symbol": "",
     "cost_usd": 111.95,
     "proceeds_usd": 82.82,
     "value_usd": 0.0,
     "profit_usd": -29.13,
     "multiple": 0.74,
     "buys": 2,
     "sells": 2,
     "first_buy_ts": 1788216882,
     "last_trade_ts": 1788216976,
     "launched_ts": null,
     "first_buy_sig": "58eoKhe8RDeSk7pE7RtfajFWCs9iM6WvrSGFhhhjbsMaCpp314u31YRevuXYSdxdpvUWhEUtJRrF356sr3bUm3E5",
     "verified": false,
     "flags": []
    },
    {
     "mint": "GtprSoXjTHG7MoYbdtpND36e1QKBH2KdKKPCMzibW9LP",
     "symbol": "",
     "cost_usd": 78.44,
     "proceeds_usd": 47.41,
     "value_usd": 0.0,
     "profit_usd": -31.03,
     "multiple": 0.6,
     "buys": 2,
     "sells": 1,
     "first_buy_ts": 1788216726,
     "last_trade_ts": 1788216792,
     "launched_ts": null,
     "first_buy_sig": "5XzcPdmRrW6Vngmp3QyzzPK35Nicio7yqHkXvAkmW1B3y5RLFj7GDWoBJ9kzhiJ8b6VRkzSupwU1qYut1ZSRmWuq",
     "verified": false,
     "flags": []
    },
    {
     "mint": "2QChDZRA76jXfmMt6t1GC6SjsmUkpiD6jzimy4jHKPAD",
     "symbol": "",
     "cost_usd": 22.57,
     "proceeds_usd": 19.22,
     "value_usd": 0.0,
     "profit_usd": -3.35,
     "multiple": 0.85,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788215929,
     "last_trade_ts": 1788216057,
     "launched_ts": null,
     "first_buy_sig": "xrMCoibcNucGdRwFpYu36ArETPWwpA3gnvU8Hk6Y8gCQSPnTT4QNRot2roJGcC1CSyp7odxnNCxh8zRgEYD2zXp",
     "verified": false,
     "flags": []
    },
    {
     "mint": "CWf2J9WbENSsbViomtZwkdvhH4JbvBepztiPqzn3pump",
     "symbol": "",
     "cost_usd": 22.57,
     "proceeds_usd": 20.08,
     "value_usd": 0.0,
     "profit_usd": -2.49,
     "multiple": 0.89,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788214635,
     "last_trade_ts": 1788214640,
     "launched_ts": null,
     "first_buy_sig": "4MuUJDqYmY1iMZq6iMmErVDsTWnhmbkMU6rudYkGTzpRQExA97mFr6V2ChzvnQLG3HTKSEXmtNYHg8RebK8XwaKU",
     "verified": false,
     "flags": []
    },
    {
     "mint": "5UoqrG1Aasu7VLE5yubK9YcfUgc4TYaetnA3k48K7M2W",
     "symbol": "",
     "cost_usd": 39.32,
     "proceeds_usd": 34.99,
     "value_usd": 0.0,
     "profit_usd": -4.33,
     "multiple": 0.89,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788214385,
     "last_trade_ts": 1788214394,
     "launched_ts": null,
     "first_buy_sig": "J3rA6AMZK5vu2qWwqLUAQJQXdUfsCwwAdthBN9kCBEKk6uFJ3bQVcQmAKvru4YpYiHbhWbKWmxGF6itHXKv4urV",
     "verified": false,
     "flags": []
    },
    {
     "mint": "CKBE3nYxjV29wY2WFcmGAPQyekvWmj3MGX5r1mgNpump",
     "symbol": "",
     "cost_usd": 392.34,
     "proceeds_usd": 312.09,
     "value_usd": 0.0,
     "profit_usd": -80.25,
     "multiple": 0.8,
     "buys": 5,
     "sells": 5,
     "first_buy_ts": 1788213193,
     "last_trade_ts": 1788216009,
     "launched_ts": null,
     "first_buy_sig": "ib5kLHWhehP7voH7BkUxTbdxhdu5JrmNWM4k2RejVVtxYk3WrAPaRCgZaKzq7Ppm6CDcyPTSW9kU7iUrD5fNt6N",
     "verified": false,
     "flags": []
    },
    {
     "mint": "eoAHM5xZeT1VwivG1CKusHJeuPHzpyUKRa8PywCpump",
     "symbol": "",
     "cost_usd": 45.06,
     "proceeds_usd": 32.89,
     "value_usd": 0.0,
     "profit_usd": -12.17,
     "multiple": 0.73,
     "buys": 2,
     "sells": 2,
     "first_buy_ts": 1788212684,
     "last_trade_ts": 1788212721,
     "launched_ts": null,
     "first_buy_sig": "3KwFitbUz42uDGvrzULTN9PRerDMWYTLdzu8qw8V7vKuAEBsAi9qmpCSWTc5y6qpSyhjoaWgbCxBEdFn91Zej95d",
     "verified": false,
     "flags": []
    },
    {
     "mint": "4R9HJzErEjAWnJqF3NkErLRapBrVB5YgP6hMyXewpump",
     "symbol": "",
     "cost_usd": 39.43,
     "proceeds_usd": 65.6,
     "value_usd": 0.0,
     "profit_usd": 26.17,
     "multiple": 1.66,
     "buys": 1,
     "sells": 2,
     "first_buy_ts": 1788212570,
     "last_trade_ts": 1788212619,
     "launched_ts": null,
     "first_buy_sig": "2PbFK9LQyQRiqaZkjkSKamyrSAwt1nas8Jue2gkGRs3592qsDhuDZfDYdFGEWjpYLXgq9AR12Ero32GK7wa8L1xE",
     "verified": false,
     "flags": []
    },
    {
     "mint": "Ehs93sc9cjZAEr2wJLtngVxUMvLVMLoUiZP9fe5Epump",
     "symbol": "",
     "cost_usd": 39.43,
     "proceeds_usd": 29.19,
     "value_usd": 0.0,
     "profit_usd": -10.25,
     "multiple": 0.74,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788212420,
     "last_trade_ts": 1788212438,
     "launched_ts": null,
     "first_buy_sig": "2YZNWjZ86oqTyNXnZLrerbs1acTazEq94hS9wSYSK5Z6zeNwAsxX6XsrHxztcRuMWVpG4G8ZWyUgcwiSXBS1Ub4t",
     "verified": false,
     "flags": []
    },
    {
     "mint": "7c328ZXKKaf7sdAm46Mp7r7A3PNqZqnMSPVWGgGgpump",
     "symbol": "",
     "cost_usd": 84.28,
     "proceeds_usd": 38.29,
     "value_usd": 0.0,
     "profit_usd": -45.98,
     "multiple": 0.45,
     "buys": 3,
     "sells": 3,
     "first_buy_ts": 1788211950,
     "last_trade_ts": 1788212082,
     "launched_ts": null,
     "first_buy_sig": "2ZyF53211zuqATEC5rRW9amn43ft9r6fPWpMepFVDar6UrVG3J5Sm8fvSpnGELqiJdV744cSMi4rwXpCpSWZfywa",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9mzY9rx8mxzWyH1ZjPEJFJDVzApevSVMPcMZYzb7sNkq",
     "symbol": "",
     "cost_usd": 39.43,
     "proceeds_usd": 29.57,
     "value_usd": 0.0,
     "profit_usd": -9.86,
     "multiple": 0.75,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788211249,
     "last_trade_ts": 1788211265,
     "launched_ts": null,
     "first_buy_sig": "4m9Sd72QdnP93FvLHzBc2EhZKgvxQLRvXKR7V3BM6jNMeyWksAHZyjdRLDHCR4Cxsr98BFZxrM6Eeg3zfXXt8gmC",
     "verified": false,
     "flags": []
    },
    {
     "mint": "HYhsMpWm2YWxpH8tHc3QdgAXYoSGh5TEDZX3rFehiVSX",
     "symbol": "",
     "cost_usd": 39.64,
     "proceeds_usd": 45.38,
     "value_usd": 0.0,
     "profit_usd": 5.74,
     "multiple": 1.14,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788210798,
     "last_trade_ts": 1788210818,
     "launched_ts": null,
     "first_buy_sig": "jnPmLNce5z9gjr6DwHq8cjE5HqujKxx9mK9ZBkbBfw9tCUJ8MiUa82MHRBWiZpd7guHTRaCjZRh5rzaaWSRUWpy",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9zgcyrfSEZMdwqLvbZxtC5T1XGbpvJbkotZgeatMpump",
     "symbol": "",
     "cost_usd": 112.68,
     "proceeds_usd": 165.74,
     "value_usd": 0.0,
     "profit_usd": 53.06,
     "multiple": 1.47,
     "buys": 2,
     "sells": 3,
     "first_buy_ts": 1788210761,
     "last_trade_ts": 1788210999,
     "launched_ts": null,
     "first_buy_sig": "26fvwqXey9A7cvJJPeJxakXgPZGG38CQTgrEniDENx9FJkbGGKj9WeRzUuGkyrw6XWerQk15in6HDkYwCTpNnvJA",
     "verified": false,
     "flags": []
    },
    {
     "mint": "3EGycnMhCeGU5gieWcx3rPYh8jPhFtVkF8u1aPA7CARD",
     "symbol": "",
     "cost_usd": 61.83,
     "proceeds_usd": 11.47,
     "value_usd": 0.0,
     "profit_usd": -50.37,
     "multiple": 0.19,
     "buys": 2,
     "sells": 1,
     "first_buy_ts": 1788210682,
     "last_trade_ts": 1788210770,
     "launched_ts": null,
     "first_buy_sig": "3QPc33KSMrRRod1HbniLeCFZq8EPhrVCyLTyaZdVYb5eiEmt2TzhAKqHFf7vJUY5moTDp8gVdWsyHSXawL33tTnV",
     "verified": false,
     "flags": []
    },
    {
     "mint": "72mAwoxXEuN8PvhwxsTvuH2UUdwSE9ZhfXBfyQG5pump",
     "symbol": "",
     "cost_usd": 42.41,
     "proceeds_usd": 30.5,
     "value_usd": 0.0,
     "profit_usd": -11.91,
     "multiple": 0.72,
     "buys": 3,
     "sells": 1,
     "first_buy_ts": 1788204600,
     "last_trade_ts": 1788204917,
     "launched_ts": null,
     "first_buy_sig": "4DkWGAG3U1FkJZWgzW2HXyejq36UxrVKRUVaUS3PVAk47CnuMTfL9Pqv93CAb8tpMFtfeDHy4LYiJWEicUnZirFm",
     "verified": false,
     "flags": []
    },
    {
     "mint": "4MB4Bse4mZXNSS5K3dbuZvuqT1FsCAx2Xvge5SEkpump",
     "symbol": "",
     "cost_usd": 22.71,
     "proceeds_usd": 16.02,
     "value_usd": 0.0,
     "profit_usd": -6.69,
     "multiple": 0.71,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788203060,
     "last_trade_ts": 1788203082,
     "launched_ts": null,
     "first_buy_sig": "5EtQdAse1Djpaz2tnv4xrzaqAWuxhyxSnsVEtpA1KNctbhvkuMSTPU1utHNHK88SFvkLivGHPQ393ndccgwZxFo5",
     "verified": false,
     "flags": []
    },
    {
     "mint": "4UXXSw9HHDzEUgXTLxz1XR4PCY1dYExiikc2XK33pump",
     "symbol": "RAC",
     "cost_usd": 22.71,
     "proceeds_usd": 16.48,
     "value_usd": 0.0,
     "profit_usd": -6.22,
     "multiple": 0.73,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788202905,
     "last_trade_ts": 1788202915,
     "launched_ts": 1788202869,
     "first_buy_sig": "4w3PMXkcMgzT38yny8m2WNhFvTwAFuJCPEBcmwmjS2HrPJxAKexa6GYHdja9rYC464Hf46s2maTJm5jT6kiBkhF7",
     "verified": false,
     "flags": []
    },
    {
     "mint": "EYBMhikmdqUs6j5p9mv1tfPY3HszsCyYeRpwme6Bpump",
     "symbol": "VOXIE",
     "cost_usd": 118.46,
     "proceeds_usd": 149.73,
     "value_usd": 0.0,
     "profit_usd": 31.27,
     "multiple": 1.26,
     "buys": 3,
     "sells": 2,
     "first_buy_ts": 1788202792,
     "last_trade_ts": 1788203195,
     "launched_ts": 1788202784,
     "first_buy_sig": "2Bqs8uBKGhiVoJC3xBvdSq9tKEUKv5FJXkv6EP1mtjzezD83XuZfZ8qaa77GjSNgSrTDa1S7zgXrEUWgGaavrKd2",
     "verified": false,
     "flags": []
    },
    {
     "mint": "GA2MrviqbPS56UFnJCJyuvdQaD1nc5TwH4i4mEjHpump",
     "symbol": "",
     "cost_usd": 56.42,
     "proceeds_usd": 43.79,
     "value_usd": 0.0,
     "profit_usd": -12.63,
     "multiple": 0.78,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788202341,
     "last_trade_ts": 1788202381,
     "launched_ts": null,
     "first_buy_sig": "4aTRgxf7kwyRHdxd5BFx7ofyQm5f12wNCADXa7hYYmqcALnqkh7ftZAKNbEF8Wx1m1piRXurynZWd3LMYuVLudH4",
     "verified": false,
     "flags": []
    },
    {
     "mint": "445dnMcvhNP25JW8Pie9BA4f9kmp3hQAUWEEQ8x6pump",
     "symbol": "",
     "cost_usd": 56.42,
     "proceeds_usd": 46.76,
     "value_usd": 0.0,
     "profit_usd": -9.65,
     "multiple": 0.83,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788201910,
     "last_trade_ts": 1788201918,
     "launched_ts": null,
     "first_buy_sig": "3RG7Kec7cRPZcY1UU3zyeAH1HCMVi85qaqtp4HF2dFVSw2cKNhAmeYyXDjbFmXXsH4zv5MFuYUjbB6v43mffbkCG",
     "verified": false,
     "flags": []
    },
    {
     "mint": "Gg7us9rAynPs1KEFLEhjkxxoRvT6V78Q1U2ojbdnpump",
     "symbol": "",
     "cost_usd": 151.97,
     "proceeds_usd": 127.43,
     "value_usd": 0.0,
     "profit_usd": -24.54,
     "multiple": 0.84,
     "buys": 3,
     "sells": 2,
     "first_buy_ts": 1788201199,
     "last_trade_ts": 1788202392,
     "launched_ts": null,
     "first_buy_sig": "dnSjRXxP2kTyUy2AhmsY6hBkMaspyd2GupnRzsXkQnQVtvuJMtjyaCCLnZvwAhGH2pEMQUWyLqf6EYvMshHW4t5",
     "verified": false,
     "flags": []
    },
    {
     "mint": "73q7NoVCrHk9Yet1FVmpyDL6jRXjShZ7xHZ5gaJSpump",
     "symbol": "",
     "cost_usd": 56.42,
     "proceeds_usd": 72.22,
     "value_usd": 0.0,
     "profit_usd": 15.8,
     "multiple": 1.28,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788200757,
     "last_trade_ts": 1788200790,
     "launched_ts": null,
     "first_buy_sig": "3nGU1NfKNp6RJ7EGQZpqDgmgmjB687aK2rAxmbJgQ9tQrj5KMnjscMojQCZcCyP86vJVdBBJb5tFQaDCxRkDJp8F",
     "verified": false,
     "flags": []
    },
    {
     "mint": "3udkwzkREsw3oGAq2frAwYNd7212VV8XmmASRs2Bpump",
     "symbol": "",
     "cost_usd": 111.7,
     "proceeds_usd": 102.56,
     "value_usd": 0.0,
     "profit_usd": -9.14,
     "multiple": 0.92,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788197317,
     "last_trade_ts": 1788197351,
     "launched_ts": null,
     "first_buy_sig": "3YpAbF6F3L1TGeY8UgNPHBTWAjp61rrnJMTAPy6YXhi5u4yHJxEXubFzeLWTuTb36MMBt8zmZhSiTXSGyoh8rN34",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9fQPAW1cC6HZXRjB59iTzcbzZULZfykF542Lt9THpump",
     "symbol": "",
     "cost_usd": 385.39,
     "proceeds_usd": 428.23,
     "value_usd": 0.0,
     "profit_usd": 42.84,
     "multiple": 1.11,
     "buys": 9,
     "sells": 12,
     "first_buy_ts": 1788196551,
     "last_trade_ts": 1788197179,
     "launched_ts": null,
     "first_buy_sig": "3dZx4JPBhZEtJvN4Wp7Mb1WYqcxssqPpZxhzG3DtFLPKtHSU1KroDJ8BqsJkkEWN8s85dakaCS9WRRNtCVYGtfNd",
     "verified": false,
     "flags": []
    },
    {
     "mint": "2uFpgZ6HnoJPRqvgRXGwp2zu9xFn84iDDWEnKXFxrSEV",
     "symbol": "",
     "cost_usd": 195.33,
     "proceeds_usd": 246.41,
     "value_usd": 0.0,
     "profit_usd": 51.07,
     "multiple": 1.26,
     "buys": 5,
     "sells": 4,
     "first_buy_ts": 1788196034,
     "last_trade_ts": 1788196463,
     "launched_ts": null,
     "first_buy_sig": "47WbWWSuD5LHAhQBCxjheu9pk58GfqH31nD7HqwyW4MJJSHihTz33Pc3j6BCaDP7YMZyQJTr1FCBzh2Q6TXntRAT",
     "verified": false,
     "flags": []
    },
    {
     "mint": "CGD5dYy9qaqxuiF4JBPjTcWyF6y2uZ3KgLBPVav4pump",
     "symbol": "",
     "cost_usd": 22.66,
     "proceeds_usd": 26.54,
     "value_usd": 0.0,
     "profit_usd": 3.88,
     "multiple": 1.17,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788193925,
     "last_trade_ts": 1788193947,
     "launched_ts": null,
     "first_buy_sig": "4DiDR7y7S3FPVNPx1yUNAxiLhZ5mjUfAdy8M2puQWAVeUhj2u5tR1pRkv19v7TAsLDEDGFctToYuxX2tMhFMvXsu",
     "verified": false,
     "flags": []
    },
    {
     "mint": "BCZPtXQwwL9oqSSF8YTykcCJHpkqk8TWEDtNdyGupump",
     "symbol": "",
     "cost_usd": 55.76,
     "proceeds_usd": 56.08,
     "value_usd": 0.0,
     "profit_usd": 0.32,
     "multiple": 1.01,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788193728,
     "last_trade_ts": 1788193732,
     "launched_ts": null,
     "first_buy_sig": "3fbGmoaNEFhMrhDH3GgXL4wwVCnGCE9dpx56MjVTPFCUSJypuxF6t9usLEcpQgfGaqvigK8LKUaDNEDEEukw41Sc",
     "verified": false,
     "flags": []
    },
    {
     "mint": "8wb2F6VRtTce17Hi1n9hSvTeM1U4Wjd8LMapYd4Epump",
     "symbol": "",
     "cost_usd": 22.45,
     "proceeds_usd": 19.49,
     "value_usd": 0.0,
     "profit_usd": -2.95,
     "multiple": 0.87,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788193694,
     "last_trade_ts": 1788193713,
     "launched_ts": null,
     "first_buy_sig": "4sSE5xG1cD6HboKX4WqpZrV7uGfKVfFZbmwc53Pc8S5Tzi6qut5SXwrNgGdspdcj16C7k3J4BXKmRoSZJNoc6g1N",
     "verified": false,
     "flags": []
    },
    {
     "mint": "DCunNZU5bbw3dgp44apcKYzgtj6vmfzfQWCcxsFKpump",
     "symbol": "",
     "cost_usd": 55.97,
     "proceeds_usd": 59.08,
     "value_usd": 0.0,
     "profit_usd": 3.1,
     "multiple": 1.06,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788193405,
     "last_trade_ts": 1788193425,
     "launched_ts": null,
     "first_buy_sig": "4yCDQqdkRXCUPbsegSuPegtFpiQNjtYzAZZeP1gkywvjmbaPuP8RkUbxvk1iKsZAAft29Ewe5mQTeUoSL9kA4UHn",
     "verified": false,
     "flags": []
    },
    {
     "mint": "5B45JxmtBUEn9E1dzAaAs3j2RpPMhxvEqTx9mJX3pump",
     "symbol": "",
     "cost_usd": 55.76,
     "proceeds_usd": 42.25,
     "value_usd": 0.0,
     "profit_usd": -13.51,
     "multiple": 0.76,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788193286,
     "last_trade_ts": 1788193303,
     "launched_ts": null,
     "first_buy_sig": "2wCN7dZmsMQTKogzxLEEgyDqzvb8u4VwBmgUgr2Dz5oSmUHtEbz6v3EHc7AocRrKvgu23diyaAaqUV3YgGmtNDr2",
     "verified": false,
     "flags": []
    },
    {
     "mint": "5kD6NRRcUY2EXJcPjJRYgXTKbNFYtvzncQQfHQCubonk",
     "symbol": "",
     "cost_usd": 14.59,
     "proceeds_usd": 8.91,
     "value_usd": 0.0,
     "profit_usd": -5.68,
     "multiple": 0.61,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788191052,
     "last_trade_ts": 1788191077,
     "launched_ts": null,
     "first_buy_sig": "5ThpGdWBG7MSsnjEtYZ51zt17A8RNKvfDLvJ43ivoWDzwGYNpEYP1WpRQ3WA8JYBBryUuPi1SkLyqgWre7BdCw1v",
     "verified": false,
     "flags": []
    },
    {
     "mint": "5mLRwZ9YAWfoBv2WdPTUPKXTHkN7VKP7Z6aqkESfpump",
     "symbol": "FINORA 2.0",
     "cost_usd": 39.23,
     "proceeds_usd": 36.56,
     "value_usd": 0.0,
     "profit_usd": -2.67,
     "multiple": 0.93,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788190642,
     "last_trade_ts": 1788190700,
     "launched_ts": 1790059370,
     "first_buy_sig": "4k5bNicjgGJyCzqBsyRaqhG3eAFR8dav24B1Vjj773hMi4kC9CYdeo71WeCSLLF6kBNxqkNkCArSyiYsYBn7kNDX",
     "verified": false,
     "flags": []
    },
    {
     "mint": "5G5NdzSwC2cKHbJaar1LibVzNvP8La1BC4zfpFUyjPMP",
     "symbol": "",
     "cost_usd": 22.52,
     "proceeds_usd": 16.01,
     "value_usd": 0.0,
     "profit_usd": -6.51,
     "multiple": 0.71,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788190623,
     "last_trade_ts": 1788190634,
     "launched_ts": null,
     "first_buy_sig": "4QyHfJbZGXQLFtkLueyvau2dkMBak82BbxeGnec7ix9Hz31LkVcf9DGYonAESJa8aF1y9bsrmT3AsBSsDW8eqgK5",
     "verified": false,
     "flags": []
    },
    {
     "mint": "4ZmBsSHc5qUL2Ucpk42hrFvYAwS3Df2gEQ2YhjiUpump",
     "symbol": "",
     "cost_usd": 83.85,
     "proceeds_usd": 71.06,
     "value_usd": 0.0,
     "profit_usd": -12.79,
     "multiple": 0.85,
     "buys": 3,
     "sells": 2,
     "first_buy_ts": 1788190194,
     "last_trade_ts": 1788190888,
     "launched_ts": null,
     "first_buy_sig": "2iFPuZBPJCGihf8yebB2JfWtMYvGakLRVRH2ZE11cdF1TK7royXp99rEQYXyA1rpxn5t7CrzakjW1ZTipybkAL7g",
     "verified": false,
     "flags": []
    },
    {
     "mint": "9NMQjV8PVxx8rDxym1fG3Dbc8D2YFwWUZKYQ9VU6pump",
     "symbol": "",
     "cost_usd": 36.38,
     "proceeds_usd": 52.01,
     "value_usd": 0.0,
     "profit_usd": 15.63,
     "multiple": 1.43,
     "buys": 2,
     "sells": 2,
     "first_buy_ts": 1788184810,
     "last_trade_ts": 1788184956,
     "launched_ts": null,
     "first_buy_sig": "2ukK5sS9LqJSBakrZuv9V8T4tYc9E5hiLVYA45ShQykKWJN3jNoVn5TQ1x4R7vNbpQnr9Nzmawxg51iJFJhy33jr",
     "verified": false,
     "flags": []
    },
    {
     "mint": "FugcQ7BDV99xiqfNVaarCEijJ8spvmy5CcFQEjopjwYD",
     "symbol": "",
     "cost_usd": 39.08,
     "proceeds_usd": 39.42,
     "value_usd": 0.0,
     "profit_usd": 0.33,
     "multiple": 1.01,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788133928,
     "last_trade_ts": 1788133945,
     "launched_ts": null,
     "first_buy_sig": "4Umd6gAo2CoKkvDJDZQMLDMcYtWWZpcA7v6ikdT4s9LMuv6TBRa5cEqnKU6UfW4ZF84CDLWmNeb9gHZYyGX26aqr",
     "verified": false,
     "flags": []
    },
    {
     "mint": "7TBkWkqohDZEoCAh1ykErGKyZzgFUEjxTv75xQeAvTeP",
     "symbol": "APEC",
     "cost_usd": 124.46,
     "proceeds_usd": 514.77,
     "value_usd": 0.0,
     "profit_usd": 390.32,
     "multiple": 4.14,
     "buys": 3,
     "sells": 5,
     "first_buy_ts": 1788133617,
     "last_trade_ts": 1788135124,
     "launched_ts": 1788134399,
     "first_buy_sig": "4Qiy8WNnXXXUvRFjACkqfgoFGLUFfwDksErKaLSmBfqPZ7rycXGhzSdQqixDyUvrx3TbfBUQhkX3NmdgQMpV6Rhp",
     "verified": false,
     "flags": []
    },
    {
     "mint": "FbJs3cnqUMYkxka9C3nmEQjBJbsHNtNZr14EnGRhJhLA",
     "symbol": "",
     "cost_usd": 119.85,
     "proceeds_usd": 123.06,
     "value_usd": 0.0,
     "profit_usd": 3.21,
     "multiple": 1.03,
     "buys": 5,
     "sells": 2,
     "first_buy_ts": 1788133134,
     "last_trade_ts": 1788134505,
     "launched_ts": null,
     "first_buy_sig": "4fqCK2Xthcc1CVDQiq5wGDHMrvarJhnaBChv11KPrUZYB71zC5uP2wXTanzhvTGLZKSxoEg5sHV1z6E3A4stHH7w",
     "verified": false,
     "flags": []
    },
    {
     "mint": "77KNYKJTi1emqEEcRYALXRVTekpYmPawP8TaChWfpump",
     "symbol": "",
     "cost_usd": 14.11,
     "proceeds_usd": 18.99,
     "value_usd": 0.0,
     "profit_usd": 4.88,
     "multiple": 1.35,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788133007,
     "last_trade_ts": 1788133171,
     "launched_ts": null,
     "first_buy_sig": "419nrphdPaDnP9ppmAN1sK9Kcbws1CgDHTQ9KxtegLeMXbkBDNQa7n4GSeyzXkS2WGW9FohkhnyGWSQeCLcqd2vc",
     "verified": false,
     "flags": []
    },
    {
     "mint": "HcRLc9VDgjLeK154xDawfb1dmVJ98DoSqcwTHGqiDeJR",
     "symbol": "ZCAT",
     "cost_usd": 93.92,
     "proceeds_usd": 93.8,
     "value_usd": 0.0,
     "profit_usd": -0.12,
     "multiple": 1.0,
     "buys": 2,
     "sells": 2,
     "first_buy_ts": 1788132933,
     "last_trade_ts": 1788134596,
     "launched_ts": 1788132595,
     "first_buy_sig": "4kTNUbcYVmcJVvAzDHMHEpQ6EQEFSRkHstXSPMvertRRpGn74B59MhuomvVtgEsU9ZGFSDMXLJ9uYvjo2pfTDuAr",
     "verified": true,
     "flags": []
    },
    {
     "mint": "DUcjrSmisJATtaQY3K7LvKmCr357uWkjoSGRFnNEpump",
     "symbol": "FUKYEAH",
     "cost_usd": 77.95,
     "proceeds_usd": 81.86,
     "value_usd": 0.0,
     "profit_usd": 3.91,
     "multiple": 1.05,
     "buys": 2,
     "sells": 1,
     "first_buy_ts": 1788132134,
     "last_trade_ts": 1788133072,
     "launched_ts": 1788276645,
     "first_buy_sig": "25vEak5hbZ8UrMR3TdC5QLiyQmi9rZkZgTKZdtCbLskmkN9NbAdPWr9sAMuzzBtkPqtus361XEVu3RZZ61b8nxcg",
     "verified": false,
     "flags": []
    },
    {
     "mint": "CDygyJyPD518nvC1Br2b3Gd1czgYKZzprz1kbBLpump",
     "symbol": "",
     "cost_usd": 39.08,
     "proceeds_usd": 40.0,
     "value_usd": 0.0,
     "profit_usd": 0.92,
     "multiple": 1.02,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788132005,
     "last_trade_ts": 1788132055,
     "launched_ts": null,
     "first_buy_sig": "3NGTLvLpHKDLwHMmXkmV2msdvbcRJXrESSSPshHuLFxb2LZqv5S3K44hY5yKp6RsmpaBfU6Hw2i8ZJaoWS4SfoLb",
     "verified": false,
     "flags": []
    },
    {
     "mint": "64HTr6Csq7e5XX7eVrR78HCUnQsBQHZcLU3C1QSoBaMa",
     "symbol": "",
     "cost_usd": 66.87,
     "proceeds_usd": 65.72,
     "value_usd": 0.0,
     "profit_usd": -1.15,
     "multiple": 0.98,
     "buys": 3,
     "sells": 2,
     "first_buy_ts": 1788131449,
     "last_trade_ts": 1788131585,
     "launched_ts": null,
     "first_buy_sig": "5epdg8NYeseLqZW6LWqrQv1zJLG6KN44Y1L5ciCaR8yfGowVhVBCgPMEVzMyS7GEHNgyQfccCQGomCntQ1oujvRL",
     "verified": false,
     "flags": []
    },
    {
     "mint": "HJx3izP7Ss1LB1bDGnu19DbHUEunsNWCx1iJDEMJpump",
     "symbol": "",
     "cost_usd": 94.6,
     "proceeds_usd": 58.73,
     "value_usd": 0.0,
     "profit_usd": -35.87,
     "multiple": 0.62,
     "buys": 2,
     "sells": 2,
     "first_buy_ts": 1788131212,
     "last_trade_ts": 1788131318,
     "launched_ts": null,
     "first_buy_sig": "5aT5tdMJFt7v37J6UHudDemisu5T8dRpTMfFTYRsHgRovQ55cff6zCqXQKcsDbSHaesPxPrQXigbHK1LaY5a2j1i",
     "verified": false,
     "flags": []
    },
    {
     "mint": "GLXRZGPLCZuwr9uymkxBBKABf4yiuEQc5SbF4r4tpump",
     "symbol": "",
     "cost_usd": 112.72,
     "proceeds_usd": 46.57,
     "value_usd": 0.0,
     "profit_usd": -66.16,
     "multiple": 0.41,
     "buys": 2,
     "sells": 1,
     "first_buy_ts": 1788130455,
     "last_trade_ts": 1788131022,
     "launched_ts": null,
     "first_buy_sig": "5awZFnmX2G7E4ZodqJszaEqsdX4pWJuyBX524SJaFRwUDqecouvgWPqbDXTkxYyGLFdqSiz8KGonEXcF7r6mH7RY",
     "verified": false,
     "flags": []
    },
    {
     "mint": "3GWz28ovrh8pdjuiyTgwx9HoFSfBSWWgm1XBvb9epump",
     "symbol": "",
     "cost_usd": 56.47,
     "proceeds_usd": 56.38,
     "value_usd": 0.0,
     "profit_usd": -0.09,
     "multiple": 1.0,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788129533,
     "last_trade_ts": 1788129539,
     "launched_ts": null,
     "first_buy_sig": "5qkf9rvU7MMX98UvSrcVP4eo5yTwv4vRSP3LsBC5Gxsyk2KhEuJwFosoX3WJYw9cYY8Ubj2QAWuSXJZUyDVb5kyE",
     "verified": false,
     "flags": []
    },
    {
     "mint": "6nrCD4L8GEqgXMa4fMHQjBnv9XWfyPwsHPuyRY8npump",
     "symbol": "LQX",
     "cost_usd": 253.39,
     "proceeds_usd": 255.31,
     "value_usd": 0.0,
     "profit_usd": 1.92,
     "multiple": 1.01,
     "buys": 6,
     "sells": 2,
     "first_buy_ts": 1788127340,
     "last_trade_ts": 1788129147,
     "launched_ts": 1788127232,
     "first_buy_sig": "1dUHFT5342Qgn4xUPJ5UvHbaaK6rp6zMMoxW3Kw55zorqX7MbWUVem9eTuymgTnVH4wSNAA5La3Xtz9C5rHdmEY",
     "verified": false,
     "flags": []
    },
    {
     "mint": "D6vDjrehvXUinRPPcEoHqqxx5C5BpyzdrB8GnK4Gpump",
     "symbol": "MERTGOAT",
     "cost_usd": 57.09,
     "proceeds_usd": 53.08,
     "value_usd": 0.0,
     "profit_usd": -4.01,
     "multiple": 0.93,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788121752,
     "last_trade_ts": 1788121765,
     "launched_ts": 1788174593,
     "first_buy_sig": "61fmGmv6uAi54m1z2pR6egJRSxpTgrUkBtiiA1LJhq4F1QNPA127Nk7CEZD8RCcFaRBj6GKHzriP6fBuQR4KDBFR",
     "verified": false,
     "flags": []
    },
    {
     "mint": "AZ18K8r75tpWSyRGxM7cH8nhYkemQJzFBsrxLsW7pump",
     "symbol": "",
     "cost_usd": 14.59,
     "proceeds_usd": 16.0,
     "value_usd": 0.0,
     "profit_usd": 1.41,
     "multiple": 1.1,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788119336,
     "last_trade_ts": 1788119354,
     "launched_ts": null,
     "first_buy_sig": "4LHKcHZcWDLzxwABRjBMx2LDSPkaKKgHH764jsEeBxnwYjmCpk55cwLx7mR1SXn248xseoGUJ3Uq8YTUNeCLNxUF",
     "verified": false,
     "flags": []
    },
    {
     "mint": "C67SSEUGyi5dTu91gd5PRwGLCnVzXWUHAXXGQUV4pump",
     "symbol": "",
     "cost_usd": 40.41,
     "proceeds_usd": 22.41,
     "value_usd": 0.0,
     "profit_usd": -17.99,
     "multiple": 0.55,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788119077,
     "last_trade_ts": 1788119127,
     "launched_ts": null,
     "first_buy_sig": "c4zUTTCa6oBC9ZKFsSNTWcXGzs7v6hnjEmhMLzMsNoEBVh7YBbga41hvSSqE61FAPrusZ4PajQ2TBXZvAXXZKPf",
     "verified": false,
     "flags": []
    },
    {
     "mint": "F2nV1UNTbesV5D3rxi5BXN8rB7kRWu1xhTKwWoogpump",
     "symbol": "",
     "cost_usd": 23.41,
     "proceeds_usd": 21.55,
     "value_usd": 0.0,
     "profit_usd": -1.86,
     "multiple": 0.92,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788118577,
     "last_trade_ts": 1788118621,
     "launched_ts": null,
     "first_buy_sig": "3ar2u7BBfc8AoYJmM7VchrJVcw7sHMseuK2SntAoDBWQoWDRbBi5xQxXEJ3F34j37eLERj2Pynhj5cg4p8vnusfM",
     "verified": false,
     "flags": []
    },
    {
     "mint": "Ga4XCHAutywAPGAgiYYRqj32JdyurqgkxaDzYTo9pump",
     "symbol": "",
     "cost_usd": 39.87,
     "proceeds_usd": 30.75,
     "value_usd": 0.0,
     "profit_usd": -9.12,
     "multiple": 0.77,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788087055,
     "last_trade_ts": 1788087166,
     "launched_ts": null,
     "first_buy_sig": "2mcHHGYPnUPs34bgcuvPPVJfsYdst45FAnvubDbteCUg2Co7RJyoVVf42oB4xBdRL63s8deJtudY7vhapgQt8TBo",
     "verified": false,
     "flags": []
    },
    {
     "mint": "2aEZrcjxkDdXN1jMxgeqjiSFwpfRWLhfQ9zBkdYqpump",
     "symbol": "",
     "cost_usd": 39.81,
     "proceeds_usd": 6.33,
     "value_usd": 0.0,
     "profit_usd": -33.47,
     "multiple": 0.16,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788083418,
     "last_trade_ts": 1788083429,
     "launched_ts": null,
     "first_buy_sig": "2z1agnsztZWGw7t2FTcrdfB4SGqbAX3ZtmCy2o8XD7AX9cMbfpq9N5z8rK5DDD9GU2Hc3EFB7X2oqFQsPurt4GGw",
     "verified": false,
     "flags": []
    },
    {
     "mint": "2uzRiUqk3HNpTZ1LvtcJ9HssJD6CJJMWGs4eEGDTpump",
     "symbol": "",
     "cost_usd": 62.96,
     "proceeds_usd": 125.93,
     "value_usd": 0.0,
     "profit_usd": 62.96,
     "multiple": 2.0,
     "buys": 2,
     "sells": 3,
     "first_buy_ts": 1788044508,
     "last_trade_ts": 1788044942,
     "launched_ts": null,
     "first_buy_sig": "3g4GAa5z7WedqnxaGxhhUsPEcwczBEag6s4Q99UfVEh3GQ9zeCst636SM87vEkCPpbbedQtSjtohHBkMgVnsAw27",
     "verified": false,
     "flags": []
    },
    {
     "mint": "Hhc3DaG2SpLDmScRE5kb9NXqzzaBdtvjAkjLP3z4pump",
     "symbol": "",
     "cost_usd": 57.09,
     "proceeds_usd": 55.47,
     "value_usd": 0.0,
     "profit_usd": -1.62,
     "multiple": 0.97,
     "buys": 1,
     "sells": 1,
     "first_buy_ts": 1788043555,
     "last_trade_ts": 1788043573,
     "launched_ts": null,
     "first_buy_sig": "4Hm4myZYPeogojVgDyAWo7rMHw8MP79tsdpRA6rRHr6HZx1Gyba4A7GfNYtQTAGEawxCBTrQWbirotjTBrrUFNdi",
     "verified": false,
     "flags": []
    }
   ]
  },
  {
   "wallet": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 4 big coins: 1WIN early $52, stORE early $2,303, XFEE early $5,320"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 4,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "omegoMAe1AMY5MFKQQr3JwXVy8F4eCvmBAfcpo8XAfq",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 3 big coins: GATO early $66, HODL early $64, JEANPHIL early $133"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 3,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "SF9TGdsfTPcA3ZVmPdPtYphgzRg6ZqUY4hnjPgjD1MW",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 3 big coins: Buttcoin early $140, MANIFEST early $43, JEANPHIL early $34"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 3,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "9ryBR3SnxgGPhWsKvsfxuNHUCTt6tSpLe8wrKCShXLaq",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: ANSEM early $1,191, CLAW early $954"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "286CHN57Km41GsAnDv866WKd6YB6HPSjFgF4rGDJTRLf",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: ZCAT early $186, PAYAI early $2,817"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "826Q2KchsUYtKqem76Ccqh2sACGNDwCfVTwerQdVpPZQ",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: ZCAT early $81, RUSH early $97"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "HXEY8jSPSua9KDqP3zhWLeNw5p7qF6gg8QNw6mKwSm5U",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: ZCAT early $77, RUSH early $102"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "GHJFdDSYx1kGg7nLTDZ7B468SqHsqySZwHRSxs4DgEVk",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: ZCAT early $334, RUSH early $109"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "CHvWpTWTZXUMvWfX7jmy8vhHbAqn6YvLc8wBxXYi4KiW",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: ZCAT early $345, RUSH early $95"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "FGF7oxtVHo7PxfjvodyWb8R6VbWFYUh6DckAL7oArQcj",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: GATO early $41, RUSH early $151"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "46BUE9ukkvREkppuBMzULFLKaupZ7A3VCrHvvFnR4444",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: GATO early $74, MASK early $106"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "LfEcaUf77iEhnz6gFpLqYgDb5Uk6Ekc5n69wu7Qa9Uw",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: GATO early $44, CLAW early $24"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "EpTEt8zmLVuqed5AEQMWbi6eaycQht4z8UDYrAws71cq",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: XFEE early $948, RUSH early $998"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "BMkHjN2N8K2PdCqeC92YYjUovn9ecW4GvFpH6yDggXWJ",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: HODL early $73, JEANPHIL early $120"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "2sapuxSmfbKAziDJKTwJWtqfZoukBLKX5zeBCVdPDpz7",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: HODL early $83, JEANPHIL early $106"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "5i8rFRKn3TEWHTPC9JH7B6QQSNRmBx5TgUGiub1kAbJA",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: MANIFEST early $43, JEANPHIL early $34"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "jmemehQbZXX7QqNE7Eyi81MdTZw6cEAT6TU4Kinwtru",
   "tier": "REJECTED",
   "labels": [
    "early buyer on 2 big coins: MANIFEST early $88, JEANPHIL early $183"
   ],
   "sources": [
    "verified-early"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 2,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "Be24Gbf5KisDk1LcWWZsBn8dvB816By7YzYF5zWZnRR6",
   "tier": "REJECTED",
   "labels": [
    "Kolscan daily #1 Chairman ² ($239.5k)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 0,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "J23qr98GjGJJqKq9CBEnyRhHbmkaVxtTJNNxKu597wsA",
   "tier": "REJECTED",
   "labels": [
    "Kolscan daily #2 gr3g ($106.4k)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "early_hits_in_search": 0,
   "stats": {
    "trades": 0,
    "judged": 0,
    "open": 0,
    "gems": 0,
    "wins_min_multiple": 0,
    "losses": 0,
    "min_multiple": null,
    "median_multiple": null,
    "best_multiple": null,
    "invested_usd": 0,
    "realized_usd": 0,
    "gem_profit_usd": 0,
    "hit_rate": null,
    "unverified": 0,
    "tx_count": 3000
   },
   "reasons": [
    "too active (3,000+ transactions): bot / scalper, not a gem hunter",
    "0 winning trade(s) (5x+ on verified coins); needs 5"
   ],
   "flags": [],
   "notes": [],
   "data_source": "helius",
   "gems": [],
   "trades": []
  },
  {
   "wallet": "5hAgYC8TJCcEZV7LTXAzkTrm7YL29YXyQQJPCNrG84zM",
   "tier": "ERROR",
   "labels": [
    "Kolscan daily #3 Schoen ($35.6k)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "87rRdssFiTJKY4MGARa4G5vQ31hmR7MxSmhzeaJ5AAxJ",
   "tier": "ERROR",
   "labels": [
    "Kolscan daily #4 Dior ($34.0k)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj",
   "tier": "ERROR",
   "labels": [
    "Kolscan daily #5 Euris ($19.1k)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6HJetMbdHBuk3mLUainxAPpBpWzDgYbHGTS2TqDAUSX2",
   "tier": "ERROR",
   "labels": [
    "Kolscan daily #6 LJC ($18.9k)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t",
   "tier": "ERROR",
   "labels": [
    "Kolscan daily #7 Mitch ($13.8k)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DrJ6SnDXkEsPeGdmSs93v5rwWumv5QMvAGSZjAyWSd5o",
   "tier": "ERROR",
   "labels": [
    "Kolscan daily #8 Iced ($9,383)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "J6TDXvarvpBdPXTaTU8eJbtso1PUCYKGkVtMKUUY8iEa",
   "tier": "ERROR",
   "labels": [
    "Kolscan daily #9 Pain ($7,438)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "J9TYAsWWidbrcZybmLSfrLzryANf4CgJBLdvwdGuC8MB",
   "tier": "ERROR",
   "labels": [
    "Kolscan daily #10 Johnson ($7,011)"
   ],
   "sources": [
    "kolscan"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "J9WiAZKf8JnCkHFL8fLCCXdEgdoLjLRqU2EGsDjdqYga",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #1 @change ($1.94M PnL, 486 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "5ECuREzbvnxfrmo9cnvrcfKLgMJ7zd2ZP1C3XbPKbHhd",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #1 @change ($1.94M PnL, 486 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #2 @frankdegods ($1.21M PnL, 1849 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "A5SEXYJY4jTEi6sjMLfZs5KAP8SVFvLDPDV67GgSSZSk",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #2 @frankdegods ($1.21M PnL, 1849 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "5fkAwNVpT8A1UHEnY62VEFpqgagdoP8FYrv5ideiQp5c",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #3 @_logjam ($1.06M PnL, 587 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "ExxadAeGwmrfS3NnHxEqWX3qmVTFNXhk7DmSScUpp1t3",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #3 @_logjam ($1.06M PnL, 587 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DrxBsUd3ufx9Q8kc8Zts1SAavMccrAJcwrFzLf77d9o1",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #4 @XVentures ($409.2k PnL, 18 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DNnsNPYz1zj8hhc7amqGz3nKqRufurUEv7j4aYXB5zWH",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #4 @XVentures ($409.2k PnL, 18 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "BJVdVGjEGiGeC96iKWhBHTQP6Qdm4ADVVSPMzHa62ZvG",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #5 @lesabre ($408.0k PnL, 651 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "H3jGitWGsrMnuvsQcCJoDfS6spJGS4AKguagaa6EnfQX",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #5 @lesabre ($408.0k PnL, 651 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DxM1hfY8FQ8dNGrucuJzhJcF8KRbjk8WBwrgKvQ9spPv",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #6 @ResellCalendar ($335.1k PnL, 2016 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "7TAMgUTRR2J8iUpPVuevFRFq8oX1kmhKTx4Y4BUNF9Eb",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #6 @ResellCalendar ($335.1k PnL, 2016 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "F1a7cR49s7VsKz8XGanFBfsbNE2M91hgKkkDhDjv44w6",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #7 @airtightfish ($305.6k PnL, 216 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "CQS9RZZvrBLC5uX5NhxwYEu7wvLtBpojvHbDgGFDu4bY",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #7 @airtightfish ($305.6k PnL, 216 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "F2hA2zDVnHyDUiMQ6b3K9Gx9A2JAxJn66ASH9xZ9LqbG",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #8 @collectible ($295.7k PnL, 948 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "3YECsvhnPBRJtWcPZgTQkczufpXdcAuHgZEDmH8vyRyS",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #8 @collectible ($295.7k PnL, 948 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "5Vx9yHpQrNDoM3YPPYAbGHtHThQaYb713QuzP5oonLmd",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #9 @ThePrimeGreek ($283.0k PnL, 514 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "G2wabvFiiUBEAV4rxt5anZXhrTam2pet6Rok22Sm6TYF",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #9 @ThePrimeGreek ($283.0k PnL, 514 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "mDR91ufq4S2uSHa9E2PYL7xg4LwcQXaQFP7YK864a1z",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #10 @smol_intern ($280.2k PnL, 651 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "CJDjRAjigb3UdsjxaV7AiMchhJV6qAcc3SjrSLFyytE3",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #10 @smol_intern ($280.2k PnL, 651 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "BXNGvVv4g8XrQCgskm4J18UBMxxT9Dyo38gjFZhWESTU",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #11 @WaterySimpleBobolink ($275.6k PnL, 77 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "BCrTEXmWutwPz8qv6w1S5gDbaLnSLpXKM5kSGVWyyfxu",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #12 @remusofmars ($267.9k PnL, 1399 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "4WhFtDKcJGLoLAYbQm7iByw5h2sNQTTZF99v4y21T28L",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #12 @remusofmars ($267.9k PnL, 1399 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "CDL22EuTKoWeXpiStMWu9pLqLNSn5NkMG3nKoz1YRVUf",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #13 @Thokani ($262.8k PnL, 1980 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "CqKkAfaWHuMnszqBLcpN64VoifsEYQFFjjhj2PHnaG7d",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #13 @Thokani ($262.8k PnL, 1980 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "4WH9bN3VDzUa4kHAXxMCUvsqdpprvYXP3DejZdunTCKw",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #14 @BreakingBad ($225.5k PnL, 605 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "B4xaT8adLqGgRE2Tm6WpNPme3dJFapckgmufADMa1Exg",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #14 @BreakingBad ($225.5k PnL, 605 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "ENkZtLj1onzQRGnEeRkQfFzBeeY2dCeiQMXDzh8XbQbj",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #15 @game_for_one ($216.9k PnL, 542 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DATMkmVrFbZt7isGoxyDSpAuF9vJycpkDKwhbf978eUw",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #15 @game_for_one ($216.9k PnL, 542 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "FY919jJnaRo55UZ3H9cnm1xKi9pyEG2m2oSakBifx5PN",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #16 @Notepad_H ($212.0k PnL, 238 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "2rTpGAwaZ5o5UvKT4En4L2Q56JsuNBk5GWGhV3upW8q4",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #16 @Notepad_H ($212.0k PnL, 238 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "G2vhbPCG5jAbBjFCJnLBbGJco93r3iw1WuvmL8csvJMD",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #17 @surveillor ($210.9k PnL, 313 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "87LAffDgoMt6z48jk4ziPj1TSzULxcrannvuP18Y89mo",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #17 @surveillor ($210.9k PnL, 313 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6bxz5E93NJBXqubkT72nLzkkz9j2PMBbfPKi6qxGYXdW",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #18 @thebtcgoose ($201.3k PnL, 692 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "8MrpW1p1qwszV5KnAAdGdcXZvH9yibXz5jEGREdPiVyT",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #18 @thebtcgoose ($201.3k PnL, 692 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "Cf7qEdZzJg7uC4B3wV93UaabRXkaFrtdVjsiDTJhetNf",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #19 @jeetergriffin ($192.9k PnL, 358 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "ApPou4mC9jDrsidNRfgvQ5pLyVP2eQQhzvZdb8voKwHz",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #19 @jeetergriffin ($192.9k PnL, 358 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "BvoCFJSmrUKn37nYiEMW6CJxb9ogPRmS4fqVbuhinWQq",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #20 @nfd ($190.8k PnL, 197 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6v9F7uyrpUFFAAbbFFgAkRPMv3UbakxvTWMaRvHsqdKk",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #20 @nfd ($190.8k PnL, 197 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "C481ZKiw4TZGs4EjNkhm6TB7s17swzmqAmCcNm73vGnW",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #21 @GuavaGuy2001 ($188.8k PnL, 85 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "Exk5RKp92du872nSU88frnnDprf8Efz9BPVdAfZvUxdy",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #21 @GuavaGuy2001 ($188.8k PnL, 85 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "FhsbQzAJWVDNwaH61cTo6XkkfEsmSYMZKs9VJHH32bVG",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #22 @fibs ($171.0k PnL, 681 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "GJcMxxQf27cYv2KLA26H6VTZdPfrneZ2HmvCdvMxxZfi",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #22 @fibs ($171.0k PnL, 681 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "AABkfEfGRJQ1bVYC6J62BuND3vMVAQr5kCiZzUV4bY9R",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #23 @C1phervoyager ($170.7k PnL, 1123 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "EmFaYsznEzQ1awoTyNxU9bi7wH9z2Xp2ufTRdY8pbYYQ",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #23 @C1phervoyager ($170.7k PnL, 1123 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "8tphd2joV1ssioBwjExKdvP2mXPKX4GD4nks6RPM3gVD",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #24 @quakerrz ($170.0k PnL, 194 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "BncpJ3BZFqLLYp84QrzJykrLYQhDmx77vzWbv9asccnR",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #24 @quakerrz ($170.0k PnL, 194 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "EMeBywiv1H4V6fPjgWo78VRxZCrPtDAyf4nvF71LJvvp",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #25 @nosanityxbt ($156.9k PnL, 3025 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "BaserSFmRTAh24rMb6vxcwYHwXc4pQkspY12fkSuXVTA",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #25 @nosanityxbt ($156.9k PnL, 3025 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "HpFQLQcHuH4roUx8jEAJNUUPAJwqUAZVodGMvdSrW3Y1",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #26 @notwashed ($154.7k PnL, 288 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6H8A751gYi8TCrHTGCyEvGeW66ymhCzir2ATuutQFsK8",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #26 @notwashed ($154.7k PnL, 288 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "H2QSGECp13sFLJgdTsDtayX3dk18Dm6sQMSQKcew7Xzk",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #27 @AvgJoesCrypto ($154.0k PnL, 191 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "5zVedvk9ffJKwaoueQWKEAAAa1nutXKhaqmFxzwmvVkW",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #27 @AvgJoesCrypto ($154.0k PnL, 191 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DPAN2Vig8BokpQCCu4mtV1mTWYLS7ktKe1hHKVBcsayL",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #28 @OinkersRUs ($152.8k PnL, 740 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6pVvYMQgSUETvtUc4mBFZPxKW43k7R46jszFidbCKmWP",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #28 @OinkersRUs ($152.8k PnL, 740 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "A2vZY74JHBBwfjo3F1Bo5iiLXpABfAhmgdyfUGzABY9F",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #29 @pxblocito ($145.0k PnL, 245 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "4adD9hwgveKsfM4zHgLkEBbuPHAZetJDoigzZ6XSi8tk",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #29 @pxblocito ($145.0k PnL, 245 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6PHHrdzSesr3FM9EuP2q9p2tDrCFyGHM3LZLbdpGthGa",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #30 @atom_xyz ($144.7k PnL, 560 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "8TxELMcavVS8rpL8YutRDeuFyjNq7Z73RjuMC3nrY1b5",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #30 @atom_xyz ($144.7k PnL, 560 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "E1ba6cLZx5WftsJiXiEjpGTozort94GvFDy7MzL9Ns6j",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #31 @llonchain ($144.4k PnL, 1379 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "3ycQs8LWVVB4DeDe26qbaifECNVefMhQKuqMv4h97L2a",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #31 @llonchain ($144.4k PnL, 1379 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6bQSN4d6anoTwnE6XDPGLA9RV8cqZPeNJro4iQUsWmso",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #32 @wrld_sol ($142.2k PnL, 163 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "L1ZbujFMUoWLnA6zLzsRy2gdaNw4JEZMda4epGBBBVt",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #32 @wrld_sol ($142.2k PnL, 163 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "CEKh3LFALbngujZkoxb7DcND1K9xL7sPzs78ArKJNimn",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #33 @Greed ($141.8k PnL, 218 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "9KD1LxEXnJn4HyXZ57KdBxBzYvvRKkMXgarptz3cBzhg",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #33 @Greed ($141.8k PnL, 218 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "AhEpzb56KhW5EUbYKdV6A4MAC6hu6mptX6haRXkpeuNV",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #34 @letsdance ($141.0k PnL, 273 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "G94HLn9SuvSjyW3KEWfPJZQFCy33J59FGDASgFDVjRjV",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #34 @letsdance ($141.0k PnL, 273 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6XkGZFbSusrc7uUEQFTpbkjLpzQ5Q1JovPaZQTeBzZHz",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #35 @Roveryaps ($137.5k PnL, 643 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "GgDAijkjPdaXNdiPQyqKZuTDE6DeTXSYxrfvCjBorZst",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #36 @hihi33 ($135.1k PnL, 685 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "Bhkhub5XjRTjcoG4FnCgfNvymdhan8ZXTTbQYXfhf9rv",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #36 @hihi33 ($135.1k PnL, 685 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "3qBVJLMAWXCbW3nhz99T99in82zZeUHkbDeSDJThbN4Z",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #37 @0xleo ($132.9k PnL, 156 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DXEt2s1HjB9xYNyfCgRBoyombgtPmS21qS8YRDhP5RN7",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #37 @0xleo ($132.9k PnL, 156 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "GFDVVq2e1JUqHquzX6z8pm34iXz2pE2K9WaDcZKuDSqC",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #38 @scalps ($123.3k PnL, 788 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "8Z29CzwUewr5YQgANfDBXjPo87BqphbtTU5Xu3TywyX",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #38 @scalps ($123.3k PnL, 788 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "CxNbb41BpnvDKLWkDs3aiSZT7Q2wCpCC3eYHV62Ko8Up",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #39 @ArtofConviction ($116.4k PnL, 25 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DcbxVEezcXbCPiZKhCU3ZHeYXBfKeQxnDfCMPJ6vhUoo",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #40 @clewguo ($115.6k PnL, 89 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "CbfECPomSocQGCEdghcq1zkYEDSVUVP761QMnRXwvyD9",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #40 @clewguo ($115.6k PnL, 89 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "BFhpehgAFUcJPyM6kTY6VtWp3PQ4rcSG31cbNrew3aeq",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #41 @rawrxd ($115.6k PnL, 4 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6qX4Sqi4jDJpDC95ZA6URGSuasv1ef1btAKgF6h38YfH",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #42 @VexRex23 ($115.4k PnL, 124 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "1MZHGYQysPw3qaLX8GGFUZw9x9VKhKmnYBow1ZKLN9D",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #42 @VexRex23 ($115.4k PnL, 124 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "4HQJjSG8dUTYBud71fjW4rNBoUJDTPfnMCxsMoLyyHk8",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #43 @Gragas ($114.6k PnL, 133 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "5y6xrp3fjyZw2gfWMKPBLgeDuSPjiRXffmiaCdLYpYs9",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #43 @Gragas ($114.6k PnL, 133 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "4jXuYZRUUCWtxy5cYwx4oTBJmF73FywyAhVoPnBpmTBN",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #44 @real_y22 ($112.2k PnL, 277 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "FQVVU1zM6kj7uQcLGD3h6Afetc7NnrZg8knvJmoLLfq2",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #44 @real_y22 ($112.2k PnL, 277 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "HBMKgEgpLJicda1gpjBiQ2sTNs7NApZvMpuxiUuXUxSM",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #45 @_traderjay ($109.2k PnL, 233 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "G9kNVrM2Pk3CvVzne8JUEhWBTKbfXANJ6SstU7Wb9fnK",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #45 @_traderjay ($109.2k PnL, 233 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "9dbcLC76Cr32kkSt2ayEzkYxxptwtkyAnSYNUsnnzK8A",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #46 @xxxfomoxxx ($108.8k PnL, 1138 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "6bYPH9U4mHq6KJHvwxzRfMGFQEXBRaF3TQkkqcpmo5ve",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #46 @xxxfomoxxx ($108.8k PnL, 1138 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "GX9tvBC9NQTErzdQajY7xYf4mBtwmYFZiPTQ8iJjpMtF",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #47 @tayk4777777 ($108.1k PnL, 180 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "FYjYdpBi4pEJquQieBXNxGJriniv8sQT1TGRXJwAyzEc",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #47 @tayk4777777 ($108.1k PnL, 180 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "CSuQB2tUK9aEhvU4WgnSB5am3f2R7DP73iLMPMYssWSQ",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #48 @hehe ($106.5k PnL, 286 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "wDmcw4NRXtbNJKnDgekzYRWT8298US1MvTwejpxQSco",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #48 @hehe ($106.5k PnL, 286 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "DPUq1bDoAzHoapLaFAhH7Z3n8w8GqD4a1BwNCyivf5jc",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #49 @astaso1 ($103.1k PnL, 376 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "3FyBTtWvhzG5p1HuTDYUEFGu7eNCZAHvvRPweXWcZsiw",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #49 @astaso1 ($103.1k PnL, 376 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "316WvHCXTDJSH6PA1BQw4w4Zizky1J73hSRVCFL6U1im",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #50 @ZeMirch ($102.9k PnL, 400 trades)"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  },
  {
   "wallet": "yxkweHEpJgAacQq7vNuU9WaC1SgV26ywAwrBZo5Qzik",
   "tier": "ERROR",
   "labels": [
    "Fomo top-50 #50 @ZeMirch ($102.9k PnL, 400 trades) · in-app wallet"
   ],
   "sources": [
    "fomo-top50"
   ],
   "gem_hits_in_search": 0,
   "stats": {},
   "reasons": [
    "HttpError: HTTP 429 for https://mainnet.helius-rpc.com/?api-key=***: max usage reached"
   ],
   "flags": [],
   "notes": [],
   "gems": [],
   "trades": []
  }
 ]
};
