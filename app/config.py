
import os
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

API_MODE = os.environ.get('API_MODE')
SANDBOX_API_URL="https://api-public.sandbox.pro.coinbase.com"

QUOTE_PAIRS = ["USD", "BTC", "ETH", "USDC"]
CB_PAIRS = {
    "USD": ["BTC-USD", "ETH-USD", "LTC-USD", "BCH-USD", "EOS-USD", "DASH-USD", "OXT-USD", "MKR-USD", "XLM-USD", "ATOM-USD", "XTZ-USD", "ETC-USD", "OMG-USD", "ZEC-USD", "LINK-USD", "REP-USD", "ZRX-USD", "ALGO-USD", "DAI-USD", "KNC-USD", "COMP-USD", "BAND-USD", "NMR-USD", "CGLD-USD", "UMA-USD", "LRC-USD", "YFI-USD", "UNI-USD", "REN-USD", "BAL-USD", "WBTC-USD", "NU-USD", "FIL-USD", "AAVE-USD", "GRT-USD", "BNT-USD", "SNX-USD", "SUSHI-USD", "MATIC-USD", "SKL-USD", "ADA-USD", "ANKR-USD", "CRV-USD", "STORJ-USD"],
    "BTC": ["ETH-BTC", "LTC-BTC", "BCH-BTC", "EOS-BTC", "DASH-BTC", "MKR-BTC", "XLM-BTC", "ATOM-BTC", "XTZ-BTC", "ETC-BTC", "OMG-BTC", "ZEC-BTC", "LINK-BTC", "REP-BTC", "ZRX-BTC", "ALGO-BTC", "KNC-BTC", "COMP-BTC", "BAND-BTC", "NMR-BTC", "CGLD-BTC", "UMA-BTC", "LRC-BTC", "YFI-BTC", "UNI-BTC", "REN-BTC", "WBTC-BTC", "BAL-BTC", "NU-BTC", "FIL-BTC", "AAVE-BTC", "GRT-BTC", "BNT-BTC", "SNX-BTC", "SUSHI-BTC", "MATIC-BTC", "SKL-BTC", "ADA-BTC", "ANKR-BTC", "CRV-BTC", "STORJ-BTC"],
    "ETH": ["LINK-ETH", "BAT-ETH", "SUSHI-ETH"],
    "USDC": ["BTC-USDC", "ETH-USDC", "ZEC-USDC", "BAT-USDC", "DAI-USDC", "GNT-USDC", "MANA-USDC", "LOOM-USDC", "CVC-USDC", "DNT-USDC"]
}

CB_MARKETS = pd.read_csv("app/CB_MARKET.csv")
CB_FEES = {
    0.5: [0, 10000],
    0.35: [10000, 50000],
    0.25: [50000, 100000],
    0.2: [100000, 1000000],
    0.18: [1000000, 10000000],
    0.15: [10000000, 50000000],
    0.1: [50000000, 100000000],
    0.07: [100000000, 300000000],
    0.05: [300000000, 500000000],
    0.04: [500000000, 1000000000],
    0.5: [10000000000, -1]
}

API_KEYS_12 = [
    "d6d2aad8623d415092c2d9c4eb03b9ca",
    "365d64328b304bdcafd61695a2557c8f",
    "79ddd4c8df0545c994a09a4c312c55a3",
    "eca064abec9a4c2e918a8d0b3eefd188",
    "4c54e723511a4c82ba4913ecc83eb201",
    "a363e93f20fe441cb2b841eb5d308f8b",
    "ec71ef69985b459ab8a5e91cab44f755",
    "f8366edd731b47f9850439cb092563fd",
    "edaf1128179440109c2a1a9c05bed96e",
    "46e93970626f4f4fab13dcef9fce1d41",
    "a35deaebafdb438b9ae2f146047c77bd",
    "79ca5b105d00411b81f3a30eb80de968"
]

RSI_PERIOD = 11
BAND_LENGTH = 31
MA_LENGTH = 1
