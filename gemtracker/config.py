"""Settings: the gem-hunter rules, file locations, API keys and well-known token mints."""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"                  # internal state (candidates, watch state)
DOCS_DATA_DIR = ROOT / "docs" / "data"    # what the HTML dashboard reads
CACHE_DIR = ROOT / ".cache"
SEEDS_FILE = ROOT / "wallets" / "seeds.txt"
WATCHLIST_FILE = ROOT / "wallets" / "watchlist.txt"
GEM_TOKENS_FILE = ROOT / "wallets" / "gem_tokens.txt"

SOL_MINT = "So11111111111111111111111111111111111111112"  # wrapped SOL
# The Fomo app signs and pays gas for every trade its users make (per Bitquery's Fomo API docs),
# so a transaction paid by this wallet is a trade placed through Fomo.
FOMO_SIGNER = "AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51"
FOMO_TOP50_FILE = ROOT / "wallets" / "fomo_top50.json"

# Stablecoins count as cash (1 token = $1) when a coin is bought or sold with them.
STABLES = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
    "2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo": "PYUSD",
}

# Liquid-staking SOL: moving SOL in and out of these is staking, not a meme-coin trade.
IGNORED_MINTS = {
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": "mSOL",
    "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn": "JitoSOL",
    "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1": "bSOL",
    "jupSoLaHXQiZZTSfEWMTRRgpnyFm8f6sZdosWBjx93v": "JupSOL",
    "5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm": "INF",
    "he1iusmfkpAdwvxLNGV8Y1iSbj4rUy6yMhEA3fotn9A": "hSOL",
    "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj": "stSOL",
}


@dataclass
class Criteria:
    """The rules a wallet must pass. All money values are in USD.

    Defaults are exactly the brief: put in $100-$500 per coin, take out $100k+
    profit, at least 4 times, never a scam/loss (every trade 20x or better),
    and no other kind of trade.
    """

    entry_min_usd: float = 100.0       # smallest allowed entry per coin
    entry_max_usd: float = 500.0       # largest allowed entry per coin
    gem_profit_usd: float = 100_000.0  # profit on a single coin to call it a "gem"
    min_gems: int = 4                  # gems needed (4-5 times minimum)
    min_multiple: float = 20.0         # EVERY trade must return at least this many x
    grace_hours: float = 72.0          # trades younger than this are still open, not judged yet
    count_unrealized: bool = False     # gem profit = cash taken out (False) or incl. holdings (True)
    all_entries_in_range: bool = True  # every trade must be a $100-$500 entry ("only such trades")
    max_tokens: int = 300              # more coins than this = bot / scalper, not a gem hunter

    def as_dict(self) -> dict:
        return asdict(self)


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Read KEY=VALUE lines from .env (if present) without overriding real environment variables."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if value[:1] in ('"', "'") and value[-1:] == value[:1] and len(value) > 1:
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].split("\t#", 1)[0].strip()
            if value.startswith("#"):
                value = ""
        if key.strip() and value:
            os.environ.setdefault(key.strip(), value)


def env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def rpc_url() -> str:
    """SOLANA_RPC_URL wins, then a Helius key, then the free public endpoint."""
    url = env("SOLANA_RPC_URL")
    if url:
        return url
    key = env("HELIUS_API_KEY")
    if key:
        return f"https://mainnet.helius-rpc.com/?api-key={key}"
    return "https://api.mainnet-beta.solana.com"
