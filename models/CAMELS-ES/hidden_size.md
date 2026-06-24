# Experiment 0: Hidden Size

***Date**: 24-06-2026*

After the experiment testing the potential use of a dynamic embedding, I realised that the model depth (`hidden_size` in the LSTM) could be excesive for the task as hand. The model tends to overfit, particularly in the runs without the dynamic embedding: KGE drops 0.2 approx. between the train and validation set. I want to test whether limiting the model capacity by reducing the LSTM hidden size helps aleviating this overfitting issue.

## Benchmark

The benchmark model is a model trained during the test of dynamic embeddings: `no-de_do03_2306_174748`. This model uses the usual hyperparameters (hidden size, dropout, etc.) that I've been using so far (see Table 1).

## Experiment Setup

Together with the change in the hidden size, I will also change other hyperparameters that may help preventing overfitting:

* I will change the **optimizer** from `Adam` to `AdamW`, as it should be more stable.
* I will increase the value of the **clip gradient norm** from 0.8 to 1.0. This hyperparameter may be hiding model issues, as it removes large gradients drastically. Tuning this hyperparameter may require a specific test.

I will explore the effects of these hyperparameters together with the change in the hidden size with three runs:

1. **Benchmark**. The model trained with the usual hyperparameters and hidden size up to now.
2. **New Hyperparameters**. The same model architecture as the benchmark, but changing the optimization hyperparameters: optimizer and clip gradient norm.
3. **Reduced Sized**. A model with the new optimization hyperparameters and a reduced LSTM hidden size.

***Table 1**. Summary of the experiments. Bold letters indicate changes compared with the benchmark model.*

| **Experiment** | **Run** | **Hidden Size** | **Output Dropout** | **Optimizer** | **Initial Learning Rate** | **Clip Gradient Norm** |
| - | - | - | - | - | - | - |
| Benchmark | `../dynamic_embedding/no-de_do03_2306_174748` | 128 | 0.3 | `Adam` | 0.00005 | 0.8 |
| New Hyperparameters | `hs128` | 128 | 0.3 | **`AdamW`** | 0.00005 | **1.0** |
| Reduced Size | `hs64` | **64** | 0.3 | **`AdamW`** | 0.00005 | **1.0** |

## Evaluation Metrics

Models will be evaluated on unseen validation and test catchments across four dimensions:

* **NSE**: Overall hydrograph goodness-of-fit. It is the loss function used during training.
* **KGE**: Overall hydrograph goodness-of-fit.
* **Alpha-NSE**: Ability to capture physical variability (peaks and low-flow extremes).
* **Beta-KGE**: Quantifying systematic volume bias.
* **Pearson-r**: Assessing temporal timing and correlation.

## Expected Outcomes

* The model with improved optimization hyperparameters should be reduce overfitting and produce a smoother evolution of the loss along the epochs.
* The reduced size model should train faster. It will probably perform slightly worse in the training set, but hopefully the performance in the validation/test sets is kept. That would be an indication that this simpler model generalizes better.