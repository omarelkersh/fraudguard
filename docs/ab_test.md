# A/B test: champion vs challenger

**Question:** Does the simpler challenger (Logistic Regression without `tx_last_10min`) perform as well as the champion (Random Forest)?

**Setup:** newest 25% of transactions (250), randomly split 50/50; decision threshold 0.5; two-proportion z-test, α = 0.05.

| Metric | Champion (A) | Challenger (B) | p-value |
|---|---|---|---|
| Recall | 22/22 = 100% | 23/24 = 95.8% | 0.33 |
| False-positive rate | 1/103 = 1.0% | 27/101 = 26.7% | < 0.0001 |

**Result:** The challenger blocked far more legitimate customers (27% vs 1%), and this difference is significant (p < 0.0001). The recall difference was not significant.

**Decision:** We keep the champion in production, because blocking 1 in 4 good customers is unacceptable.

**Limitations:** There were only about 23 fraud cases per group, so the sample is too small to detect small recall differences. The data is synthetic, so real results would differ.
