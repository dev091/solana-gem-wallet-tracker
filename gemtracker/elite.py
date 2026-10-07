"""The elite meme-coin traders whose play we reconstruct.

Public figures from KOL Explorer (kolexplorer.com/kol/<slug>, 90-day stats as of
2026-10-07), the Pump.fun monthly PnL board and solana-trading.com's 2026 top-10 list.
Each address was checked active on-chain on 2026-10-07. The stats are the published
summary only; the profiler recomputes everything from chain data.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Elite:
    name: str
    wallet: str
    style: str             # scalper | fast-flip | swing
    median_hold_s: float   # published median hold
    median_entry_mcap: float  # USD
    win_rate: float | None = None


ELITES = (
    Elite("Decu", "4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9", "scalper", 14, 8_200, 0.64),
    Elite("Cented", "CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o", "scalper", 12, 5_900, 0.53),
    Elite("Trunoest", "ardinRsN1mNYVeoJWTBsWeYeXvuR9UUDGMsCDKpb6AT", "scalper", 21, 7_400, 0.62),
    Elite("Theo", "Bi4rd5FH5bYEN8scZ7wevxNZyNmKHdaBcvewdPFxYdLt", "scalper", 17, 4_800, 0.50),
    Elite("Cupsey", "2fg5QD1eD7rzNNCsvnhmXFm5hqNgwTTG8p7kQ6f3rx6f", "scalper", 17, 10_300, 0.42),
    Elite("Cooker", "8deJ9xeUvXSJwicYptA9mHsU2rN2pDx37KWzkDkEXhU6", "scalper", 9, 6_300, 0.71),
    Elite("Trenchman", "Hw5UKBU5k3YudnGwaykj5E8cYUidNMPuEewRRar5Xoc7", "fast-flip", 60, 7_700),
    Elite("Cap", "CAPn1yH4oSywsxGU456jfgTrSSUidf9jgeAnHceNUJdw", "fast-flip", 59, 17_600),
    Elite("Mr. Frog", "4DdrfiDHpmx55i4SPssxVzS9ZaKLb8qr45NKY9Er9nNh", "fast-flip", 120, 4_200, 0.935),
    Elite("Smokez", "5t9xBNuDdGTGpjaPTx6hKd7sdRJbvtKS8Mhq6qVbo8Qz", "fast-flip", 120, 16_000, 0.38),
    Elite("Frank degods", "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ", "swing", 9_360, 497_000),
)

BY_WALLET = {e.wallet: e for e in ELITES}


def name_of(wallet: str) -> str:
    e = BY_WALLET.get(wallet)
    return e.name if e else ""
