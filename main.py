#!/usr/bin/env python3
"""cbBTC dip-reversal bot for make.fun's agent-fun/bars-replay/v1 replay.

Thesis: cbBTC on the Orca Whirlpool mean-reverts after sharp multi-minute
drops.  The bot stays in cash most of the time, buys a deep 60-minute dip,
and exits on a fixed profit target, a hard stop, or a time stop.  Trading
rarely matters: a full-size round trip pays fees, slippage and price impact,
so the edge has to come from a move clearly larger than that cost.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"

# Signal and risk parameters (minutes = bars).
LOOKBACK = 60          # bars used for the dip measurement
ENTRY_DIP_BPS = 60     # buy after a 60-bar drop of at least this many bps
TARGET_BPS = 90        # take profit this far above the entry close
STOP_BPS = 200         # hard stop this far below the entry close
MAX_HOLD = 120         # time stop, in bars
COOLDOWN = 120         # bars to stay flat after an exit
MAX_SLIPPAGE_BPS = 200


class Bot:
    def __init__(self):
        self.closes = []
        self.entry_px = None
        self.entry_bar = None
        self.cooldown = 0

    def dip_bps(self):
        if len(self.closes) <= LOOKBACK:
            return 0.0
        past = self.closes[-1 - LOOKBACK]
        return (self.closes[-1] / past - 1.0) * 10000.0

    def on_batch(self, state, batch):
        for bar in batch["bars"]:
            if bar["symbol"] == SYMBOL:
                self.closes.append(int(bar["c"]))

        if self.cooldown > 0:
            self.cooldown -= 1

        close = state.close(SYMBOL)
        if close is None:
            return []

        held = state.positions.get(SYMBOL)

        if held is None:
            if self.entry_px is not None:
                self.entry_px = None
                self.entry_bar = None
            if self.cooldown > 0 or len(self.closes) <= LOOKBACK:
                return []
            if self.dip_bps() <= -ENTRY_DIP_BPS:
                cash = state.cash
                if cash < 1_000_000:
                    return []
                self.entry_px = close
                self.entry_bar = len(self.closes) - 1
                return [{
                    "side": "buy",
                    "symbol": SYMBOL,
                    "notional_quote_units": cash,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }]
            return []

        if self.entry_px is None:
            self.entry_px = close
            self.entry_bar = len(self.closes) - 1
        if self.entry_bar is None:
            self.entry_bar = len(self.closes) - 1

        gain_bps = (close / self.entry_px - 1.0) * 10000.0
        held_bars = len(self.closes) - 1 - self.entry_bar
        if gain_bps >= TARGET_BPS or gain_bps <= -STOP_BPS or held_bars >= MAX_HOLD:
            self.cooldown = COOLDOWN
            self.entry_px = None
            self.entry_bar = None
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": held.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []


def main():
    bot = Bot()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
