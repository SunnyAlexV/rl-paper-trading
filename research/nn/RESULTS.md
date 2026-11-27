# Neural nets vs simple models: results (27 Nov 2026)

Rules: `SPEC.md` (committed before the run). Same 12 inputs; target = rank of the 20-day return from the next open; train
2013-19 (90,889 stock-days), test 2020-26 (157,757, unseen). Rank IC with t (20-day targets sampled every 5 days, t
adjusted for the overlap). `nn_vs_simple.csv`.

| Model | Train IC | **Test IC (unseen)** | Drop from train to test |
|---|---|---|---|
| Momentum + delivery, no training | 0.073 | **0.052** (t 3.4) | 30% |
| Ridge regression | 0.097 | **0.059** (t 3.0) | 39% |
| Gradient-boosted trees, depth 3 | 0.142 | **0.056** (t 3.2) | 60% |
| Neural net, 1 layer | 0.120 | **0.060** (t 3.8) | 50% |
| Neural net, 3 layers | 0.137 | **0.054** (t 3.6) | 60% |
| Neural net, 5 layers | 0.174 | **0.046** (t 3.7) | 73% |

**Reading.** The more flexible the model, the better it fits the training years and the more of that fit disappears on
unseen years. The deepest network looked best in training (0.174) and was worst in the test (0.046): it learned the noise.
On unseen data, ridge and a one-layer network did slightly better than the untrained momentum + delivery blend
(0.059-0.060 vs 0.052), consistent with the finance literature (shallow models help a little, depth does not).
Caveats: one train/test split; prediction quality only, before costs, turnover and portfolio construction.
