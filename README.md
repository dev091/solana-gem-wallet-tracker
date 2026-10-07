# Solana Gem Hunter Wallet Tracker

पहले यह repo HTML practice के लिए था (वो files अब भी `First Project/` में हैं)।
अब इसमें हम **Solana meme coins के वो wallets ढूँढते और track करते हैं जो बार-बार
$100–$500 लगाकर $100k+ बनाते हैं** — और कभी scam coin में पैसा नहीं डुबाते।

## लक्ष्य: Pump.fun daily top 5 (Goal tracker)

| Command | क्या करता है |
|---|---|
| `python -m gemtracker board` | Pump.fun का official PnL leaderboard (24h / 7d / 30d, top 100) + Kolscan daily: हर rank के लिए कितना profit चाहिए, कौन से wallets बार-बार आते हैं (consistent), किसने कम पैसे से बड़ा कमाया |
| `python -m gemtracker watch` | consistent wallets + scan वाले + watchlist: हर 15 मिनट holdings की तुलना से buy/sell पकड़ता है (free RPC पर भी चलता है), alerts भेजता है |
| `python -m gemtracker paper` | **Paper trading:** हर पकड़े गए buy पर $20 का नकली trade (देर से मिली price पर, 2% fees+slippage हर तरफ़) — तीन exit rules: उनके बेचते ही बेचो / 2x पर आधा / 24 घंटे बाद। पैसा लगाने से पहले यही बताता है कि copy करना फ़ायदे का है या नहीं |

अपना wallet track करने के लिए उसका public address `wallets/me.txt` में डालो (या GitHub → Settings →
Variables → `MY_WALLET`): `board` बताएगा कि आप top 5 से कितनी दूर हो।
Dashboard के **Goal** tab में top-5 का cut-off, rank-वार chart और समय के साथ बदलाव दिखता है।

## कौन से wallets चुने जाते हैं (rules)

| Rule | Default | बदलने का flag |
|---|---|---|
| हर coin में entry | $100 – $500 | `--entry-min`, `--entry-max` |
| एक coin पर profit ("gem") | $100,000+ (असल में निकाला गया पैसा) | `--gem-profit`, `--include-unrealized` |
| ऐसे gems कितनी बार | कम से कम **4** | `--min-gems 5` |
| **हर एक** trade | कम से कम **20x** — एक भी scam / rug / loss नहीं | `--min-multiple` |
| दूसरी तरह के trades | नहीं (हर entry $100–$500 ही हो) | `--allow-other-entries` |
| ताज़ा trades (72 घंटे से नए) | अभी judge नहीं होते, "open" गिने जाते हैं | `--grace-hours` |

हर wallet को एक tier मिलता है:

- **STRICT** — ऊपर की हर शर्त पूरी करता है।
- **GEM_HUNTER** — 4+ gems हैं, पर कोई दूसरी शर्त टूटी (जैसे एक trade 20x से कम)। कारण साथ में दिखता है। ये भी track होते हैं।
- **REJECTED** — gems कम, या bot / scalper (हज़ारों transactions)।

## Wallets कहाँ से आते हैं

| Source | क्या है | Key |
|---|---|---|
| `fomo-top50` | Fomo app के top-50 profit leaderboard का snapshot (9 Aug 2026) — हर trader का main wallet और Fomo in-app wallet, दोनों check होते हैं (`wallets/fomo_top50.json`) | नहीं |
| `kolscan` | Kolscan leaderboard — Pump.fun ने Kolscan ख़रीदा है, यही उसका traders leaderboard है | नहीं |
| `pump-early` | **On-chain gem search** — Pump.fun के सबसे बड़े coins का bonding curve सीधे blockchain से पढ़कर, शुरुआती trades में $100–$500 लगाने वाले wallets; जो 2+ बड़े coins में जल्दी घुसे | नहीं |
| `fomo` | Fomo app leaderboard live (24h / 7d / 30d), unofficial [fomoapi.io](https://fomoapi.io) से | `FOMOAPI_KEY` |
| `st-kols`, `st-top` | Solana Tracker KOL leaderboard + सबसे ज़्यादा ROI वाले traders (4+ closed coins) | `SOLANATRACKER_API_KEY` |
| `gmgn` | GMGN smart-money + KOL wallets | `GMGN_API_KEY` |
| `pump-gems` | **Gem search** — Pump.fun के सबसे बड़े coins (+ `wallets/gem_tokens.txt`) में किसने $100–$500 लगाकर $100k+ निकाला, और कितने coins पर। यह सबसे सीधा तरीका है | Solana Tracker या GMGN key |
| `seeds` | `wallets/seeds.txt` — Fomo app, Pump.fun, X, कहीं से भी address ख़ुद paste करो | नहीं |

फिर हर candidate का **हर trade** check होता है: on-chain transactions से ख़ुद हिसाब (Solana RPC),
या Solana Tracker की PnL API से (key हो तो, बहुत तेज़)। Fomo app हर trade एक ही wallet
(`AgmLJBMD…zN51`) से sign करवाता है, इसलिए tool बताता है कि किसी wallet के कितने trades Fomo app से हुए।
**बिना किसी key के भी** `fomo-top50`, `kolscan`, `pump-early` और `seeds` चलते हैं।

## GitHub पर चलाना (कुछ install नहीं करना)

1. **Keys डालो** — Settings → Secrets and variables → Actions → *New repository secret*।
   Names `.env.example` में हैं। कम से कम `HELIUS_API_KEY` (free) और
   `SOLANATRACKER_API_KEY` या `GMGN_API_KEY` डालो। बिना key के सिर्फ़ Kolscan + seeds चलेंगे।
2. **Scan** — Actions → *Gem hunter scan* → *Run workflow*। रोज़ अपने-आप भी चलता है।
   Results `docs/data/wallets.json` में commit होते हैं, track होने वाले wallets `data/tracked.json` में।
3. **Dashboard** — Settings → Pages → *Deploy from a branch* → `main` + `/docs`।
   फिर `https://dev091.github.io/<repo-name>/` खोलो।
4. **Alerts** — `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (या `DISCORD_WEBHOOK_URL`) secrets डालो।
   *Gem hunter watch* हर 15 मिनट देखता है कि tracked wallets ने क्या ख़रीदा। दो या ज़्यादा tracked
   wallets 24 घंटे में एक ही coin लें तो 🔥 alert।

Scheduled workflows सिर्फ़ `main` branch पर चलते हैं। GitHub schedule कभी-कभी देर से चलाता है;
second-by-second alerts के लिए नीचे वाला `watch --loop` अपने PC / VPS पर चलाओ।

## अपने PC पर चलाना

Python 3.9+ चाहिए, `pip install` कुछ नहीं।

```bash
cp .env.example .env                          # keys भरो (सब optional)
python -m gemtracker run                      # leaderboards + gem search + scan
python -m gemtracker analyze <WALLET>         # एक wallet का trade-by-trade हिसाब
python -m gemtracker watch --loop             # real-time alerts (हर 30 सेकंड)
python -m gemtracker run --min-gems 5         # और सख़्त
python -m gemtracker run --sources seeds      # सिर्फ़ अपने paste किए wallets
python -m unittest discover -s tests -t .     # tests
```

`docs/index.html` को browser में सीधे खोल सकते हो (server की ज़रूरत नहीं)।

## Files

| Path | काम |
|---|---|
| `gemtracker/` | Python code — `sources.py` (leaderboards, gem search), `solana.py` + `trades.py` (on-chain हिसाब), `criteria.py` (rules), `watch.py` (alerts) |
| `wallets/seeds.txt` | ख़ुद के candidate wallets (Fomo top 10 वगैरह यहाँ paste करो) |
| `wallets/watchlist.txt` | ये wallets हमेशा track होंगे, scan का result कुछ भी हो |
| `wallets/gem_tokens.txt` | वो coins जिन पर 100x+ हुआ — gem search इनके traders देखता है |
| `docs/` | Dashboard (GitHub Pages) |
| `.github/workflows/` | हर 3 घंटे leaderboard snapshot, हर 15 मिनट watch + paper trading, रोज़ का gem-hunter scan |
| `data/leaderboards/` | leaderboard history (top-5 cut-off over time, wallet appearances) |
| `data/paper_ledger.json` | सारे paper trades का हिसाब |

## ज़रूरी सच

- बार-बार 200x+ और **कभी एक भी loss नहीं** — ऐसा pattern ज़्यादातर insiders (dev के अपने wallets)
  और launch के पहले second में ख़रीदने वाले snipers / bundlers का होता है, skill का नहीं।
  Tool ऐसे निशान flag करता है: *"bought within 60s of launch"*, *"sold coins it never bought"*।
- Fomo / Kolscan leaderboards के top traders ज़्यादातर high-frequency scalpers हैं — उनके सैकड़ों
  losing trades होते हैं, इसलिए "हर trade 20x" वाली शर्त पर वो fail होंगे। यह उम्मीद के मुताबिक़ है।
- जब तक आप copy करोगे, price भाग चुका हो सकता है। यह financial advice नहीं है।

## Repo का नाम बदलना

Settings → General → *Repository name* → जैसे `solana-gem-wallet-tracker` → Rename।
पुराना link अपने-आप नए पर redirect होता है। अपनी machine पर:
`git remote set-url origin https://github.com/dev091/solana-gem-wallet-tracker.git`
