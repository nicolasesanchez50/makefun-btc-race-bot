# cbBTC dip-reversal bot

Entry for make.fun's *Race a BTC trading bot live for 24 hours* competition
(`btc-race-24h-20261111-0801`).

The bot speaks `agent-fun/bars-replay/v1`: one JSON line per minute carrying a
cbBTC/USDC bar, answered with at most one buy or sell order. It holds cash by
default, buys after a 60-bar drop of at least 60 bps, and exits on a +90 bps
target, a -200 bps stop or a 120-bar time stop. Fees, 2 bps slippage and the
pool's price impact are modelled by the replay; trading rarely is deliberate,
since a full-size round trip costs about 26 bps.

`main.py` is the entrypoint (Python 3.13, standard library only).
`vendor/makefun_bars.py` is make.fun's protocol shim, copied byte for byte
from the kit's `sdk/`.
