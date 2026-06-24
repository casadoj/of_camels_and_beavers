# Experiment 1: Dynamic Embedding

***Date**: 23-06-2026*

In this experiment I want to test whether adding a **dynamic embedding** layer improves the model performance and regularization.

## Dynamic Inputs

I have increased the number of dynamic inputs:

* Precipitation: Instead of only average precipitation (`precip_mm_rocio`), I include these new variables:
    * Maximum precipitation (`precip_max_mm_rocio`).
    * Standard deviation (`precip_std_mm_rocio`).
    * Fraction of the catchment affected by precipitation (`precip_frac_rocio`).
* Temperature: Apart from the average temperature (`temp_degC_rocio`), I include these new variables:
    * Diurnal temperature range (`temp_dtr_degC_rocio`).

As in previous runs, I also include the average potential evapotranspiration (`pet_mm_rocio`) and the encoders of the day of the year (`doy_sin` and `doy_cos`). In total, there are 9 dynamic inputs.

## Dynamic Embedding

The architecture of the dynamic embedding layer is a multi-layer perceptron (MLP) of two layers. The first layer expands the number of channels from 9 to 32, and the second layer compresses it back to 8 channels. These layers use `tanh` as the activation function, to avoid exploding values. This is the configuration:

```yaml
dynamics_embedding:
  type: fc
  hiddens: [32, 8]
  activation: tanh
  dropout: 0.1
```

The dynamic embedding layer smoothes the loss landscape, which allows us to reduce the regularization hyperparameters, namely the `output_dropout`, which in previous runs was set at 0.5. Also, the smoother loss landscape requires a change in the learning rates, which are reduced to a starting value of 0.00005, instead of 0.0001.

## Experiment Setup

I run three experiments to assess how adding the dynamic embedding influences results:

1. **Dynamic embedding**. The setup defined above.
2. **No dynamic embedding and dropout 0.3**. Identical setup as experiment 1, removing the dynamic embedding layers.
3. **No dynamic embedding and dropout 0.5**. A setup closer to previous runs, as the reduction of the dropout rate could hinder the performance of the model without dynamic embedding.

***Table 1**. Summary of the experiments.*

| **Experiment** | **Run** | **Dynamic Embedding** | **Output Dropout** | **Initial Learning Rate** | **Clip Gradient Norm** |
| - | - | - | - | - | - |
| Dynamic Embedding | `de_do03` | `type: fc`<br>`hiddens: [32, 8]`<br>`activation: tanh`<br>`dropout: 0.1` | 0.3 | 0.00005 | 0.8 |
| No Dynamic Embedding (Ablation) | `no-de_do03` | None | 0.3 | 0.00005 | 0.8 |
| No Dynamic Embedding (Optimal) | `no-de_do05` | None| 0.5 | 0.00005 | 0.8 |

## Evaluation Metrics

Models will be evaluated on unseen validation and test catchments across four dimensions:

* **KGE**: Overall hydrograph goodness-of-fit.
* **Alpha-NSE**: Ability to capture physical variability (peaks and low-flow extremes).
* **Beta-KGE**: Quantifying systematic volume bias.
* **Pearson-r**: Assessing temporal timing and correlation.

## Expected Outcomes

* **Experiment 1 (Embedded)** is expected to converge significantly faster (fewer epochs) and demonstrate the tightest generalization gap between training and validation scores.
* **Experiment 2 (No Embedding, 0.3 Dropout)** is expected to suffer from overfitting due to the raw, collinear dynamic inputs.
* **Experiment 3 (No Embedding, 0.5 Dropout)** will isolate whether a higher dropout rate can compensate for the lack of structural feature embedding.