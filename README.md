# Trading agents on a limit-order-book exchange

Seven automated trading agents, from a simple momentum rule to ARIMA, SARIMAX, LSTM and a
simplified Gjerstad-Dickhaut agent. They are benchmarked against standard reference traders on the
[Bristol Stock Exchange](https://github.com/davecliff/BristolStockExchange) (BSE), a
continuous double-auction market with a limit order book.

**Origin:** MSc coursework for *COMP4015 Designing Intelligent Agents*, University of Nottingham, 2022.
The agent code is the original 2022 code, uploaded in 2026. The changes made in 2026 so it runs today
are listed under [What changed in 2026](#what-changed-in-2026).

- [Report](docs/report.pdf): design, experiments, results and discussion
- [Extended review](docs/extended-review.pdf): market terminology, BSE internals and model maths
- [Slides](docs/slides.pdf)

## The market

BSE simulates one commodity traded in a continuous double auction. Buyers post bids and sellers post
asks at any time, and the limit order book (LOB) keeps both sides sorted best-to-worst. A trade
happens when a bid meets an ask. Every trader receives customer orders with a private **limit price**
it must never cross. A trader's profit is the gap between its limit and the price it trades at.

## The agents

My agents live in `BSE.py` beside the exchange. Each one is built from three parts: **memory** (what it
tracks from the tape), **risk** (whether to trade at all) and **pricing** (what to quote).

| Agent | Class | Memory | Pricing |
|---|---|---|---|
| Basic | `BasicTrader` | last best bid | matches the best bid when it rises in two rounds in a row |
| ARIMA | `ARIMATrader` | every best bid | `auto_arima` refit every call, predicts the next price |
| Fast ARIMA | `FARIMATrader` | every best bid | as ARIMA, but refits only when a new trade prints |
| Fast ARIMA, short-term memory | `FARIMASTMTrader` | last 100 best bids | as Fast ARIMA, on a sliding window |
| SARIMAX | `SARIMAXTrader` | every best bid | statsmodels SARIMAX (seasonal ARIMA) |
| LSTM | `LSTMTrader` | trade tape | Keras LSTM retrained every 10 trades, predicts from the last 4 prices |
| Simplified GD | `SGDTrader` | accepted *and* rejected quotes | picks the price most likely to fill, using P = (successful bids + unmet asks) / (successful bids + unmet asks + unsuccessful bids) |

The prediction-based agents compare the predicted price with their limit and the current best bid,
then outbid, match or hold. `SGDTrader` adapts the Gjerstad-Dickhaut trader from the BSE project.

**Not mine:** the exchange (`Order`, `Orderbook`, `Exchange`, `market_session` and the rest of the
simulation) and the reference traders `Trader_Giveaway`, `Trader_ZIC`, `Trader_Shaver`, `Trader_Sniper`,
`Trader_ZIP`, `Trader_PRZI`, `Trader_PRZI_SHC` and `Trader_AA` are from Dave Cliff's BSE (MIT licence,
header kept in `BSE.py`). `trialTrader` is an unused stub of mine.

## Experiments

Both experiments run in a market of 10 Shaver, 10 ZIC and 10 ZIP traders, over 6 sessions of 600
simulated seconds, with limit prices from 50 to 150.

1. **Each agent on its own** against the reference traders.
2. **All five agents together** (Fast ARIMA, Fast ARIMA short-term memory, SARIMAX, LSTM, Simplified
   GD) against the reference traders, so they also compete with each other.

### Results reported in 2022 (mean profit per session)

| Agent | Exp 1, all sessions | Exp 1, zero sessions removed | Exp 2, all sessions | Exp 2, zero sessions removed |
|---|---:|---:|---:|---:|
| Fast ARIMA | 16 | 30 | 21 | 38 |
| Fast ARIMA, short-term memory | 10 | 28 | 3 | 15 |
| SARIMAX | 17 | 34 | 21 | 54 |
| LSTM | 18 | 36 | 14 | 44 |
| Simplified GD | 21 | 36 | 15 | 35 |

The report's Experiment 1 table, and slide 18, label these two columns the wrong way round. Removing
zero-profit sessions can only raise a mean of non-negative profits, so the larger figure must be the one
with zeros removed. The table above has the labels the right way round. Experiment 2 was labelled
correctly.

**Findings:** on its own, the Simplified GD agent earned the most. It decides fastest, so it trades
more, and it learns from rejected quotes as well as accepted ones. Head to head, SARIMAX and LSTM
earned the most per profitable session, because they predicted the equilibrium price better. Across
both experiments, how quickly an agent could act mattered as much as how accurately it predicted.

`results/2022_results.csv` holds the only raw data that survived from 2022: a single partial run of 20
rows. It is not the full data set behind the tables above.

## Running it

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python Experiment.py --quick          # smoke test: one 60 s session per agent
python Experiment.py                  # both experiments, 6 x 600 s sessions (slow: ARIMA refits)
python Analysis.py                    # summarise final_results.csv
python Analysis.py results/2022_results.csv
```

`Experiment.py --help` lists options for choosing the experiment, agents, session count and length.
Requirements are pinned to versions that run the 2022 code unchanged (TensorFlow/Keras 2.15,
numpy 1.26).

## What changed in 2026

- **`Experiment.py` is a reconstruction.** The 2022 script was lost. It was rebuilt from the report and
  from the experiment set-up left commented out in `BSE.py`. Final balances come from BSE's own
  end-of-session summary and go to `final_results.csv`.
- **`Analysis.py` fixed.** It hard-coded five trader types, so the `ARIMA` rows in the saved results
  raised `KeyError`. It also wrote averages back into its session counter. It now discovers trader
  types from the data and reads both result formats.
- **`BSE.py`:** a single compatibility change. `predict(1)[0]` became `np.asarray(predict(1))[0]` in the
  three ARIMA agents, because pmdarima now returns a pandas Series indexed from the end of the data.
  Agent logic is otherwise unchanged.
- Added `requirements.txt`, `LICENSE`, `.gitignore`, `docs/` and this README.

## Known issues (left as they were in 2022)

- **Prediction agents only work as buyers.** The ARIMA, SARIMAX and LSTM pricing logic is written for
  bids: it never quotes above the limit. As a seller it quotes *below* its limit, and BSE stops the
  session with `Bad ask`. The experiments therefore place the agents on the buy side.
- **Balances in `results.csv` are recorded about 58 s into a session, not at the end.** Each agent's
  `getCount()` saves its balance once `60 - time < 2`, a leftover from 60-second test sessions. With
  600-second sessions that snapshot is taken early, which is the most likely cause of the many
  zero-profit sessions the report blamed on timing. `Experiment.py` records true end-of-session
  balances separately, in `final_results.csv`.
- The prediction agents refit their models inside the market loop, so full runs are slow.

## Licence

MIT. See [LICENSE](LICENSE). BSE is copyright (c) 2012-2020 Dave Cliff. The agents and scripts are
copyright (c) 2022-2026 Ritvik Joshi.
