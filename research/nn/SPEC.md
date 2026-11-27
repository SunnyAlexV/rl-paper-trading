# Do neural networks separate signal from noise here? (written 27 Nov 2026, BEFORE the run; run once; diagnostic)

Same 12 inputs for every model, each a cross-sectional rank (0-1) per day over the universe: 5/20/60-day return, 12-1
momentum, 20- and 250-day volatility, volume surge, size (traded value), 60-day delivery %, delivery trend, 20-day lower and
upper wick share. Target: rank of the return from the next open over 20 trading days. Samples every 5th trading day.
Train on 2013-2019, test on 2020-2026 (unseen). Models: equal-weight momentum + delivery (no training, the primary's idea),
ridge regression, gradient-boosted trees (depth 3), neural nets with 1 hidden layer (32), 3 layers (64-32-16) and 5 layers
(256-128-64-32-16), each net trained with early stopping on the last 20% of the training years.
Reported: rank IC (mean daily rank correlation of prediction with target) in training and in the test years, with t.
