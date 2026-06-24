# Experiment 2: Output Activation

***Date**: 23-06-2026*

This experiment follows the test on the use of dynamic embeddings. It uses the best model architecture in the _dynamic_embedding_ experiment and explores the effects of using a `softplus` output activation, instead of `linear`.

## Benchmark

> **MISSING**. Define here the benchmark model, i.e., the best model in _Experiment 1: Dynamic Embedding_

## Activation Functions

The `softplus` activation is a continues variant of the `relu`. It produces strictly positive outputs, but instead of a break point at $x=0$, it introduces a smooth, continuous function that produces small positive outputs for small negative inputs. In this way, it avoids the dead of neurons that may be caused by `relu`. 

$$f(x)=\log ( 1 + e^x)$$

The whole idea of using this activation is that it could reproduce better a strictly positive variable such as specific discharge, particularly thinking about intermittent rivers, which are common in wide areas of Spain.

## Experiment Setup

Using this softer activation function has implications in the magnitude of gradients, and therefore in other hyperparameters such as `learning_rate` and `dropout`. As gradients are reduced when the inputs are negative, this activation function requires a **larger learning rate** and a **smaller dropout**. 

We will explore the effects of these hyperparameters together with the change in the output activation with three runs:

1. **Benchmark**. The best model in the previous experiment:
2. **Softplus Ablation**. The same model setup as the benchmark, only changing the `output_activation` to `softplus`.
3. **Softplus Optimized**. Apart from the `softplus` activation, it uses an increased initial learning rate and a smaller dropout to find the optimal setup of this activation function.

***Table 1**. Summary of the experiments.*

| **Experiment** | **Output Activation** | **Output Dropout** | **Initial Learning Rate** |
| - | - | - | - |
| Benchmark | `linear` | 0.3 | 0.00005 |
| Softplus Ablation | `softplus`| 0.3 | 0.00005 |
| Softplus Optimized | `softplus`| 0.1 | 0.0001 |

## Evaluation Metrics

Models will be evaluated on unseen validation and test catchments across four dimensions:

* **KGE**: Overall hydrograph goodness-of-fit.
* **Alpha-NSE**: Ability to capture physical variability (peaks and low-flow extremes).
* **Beta-KGE**: Quantifying systematic volume bias.
* **Pearson-r**: Assessing temporal timing and correlation.

## Expected Outcomes

Have a particular look at the $\alpha-\text{NSE}$, as it represents the model variability, and the performance on low-flow periods.

* If **Run 2 performs worse than Run 1, but Run 3 beats both**: strong interaction trap. It means `softplus` is a better activation function, but it cannot handle a dropout as high as 0.3 at the final prediction gate because it corrupts the asymptotic behavior near zero flow.
* If **Run 2 beats Run 1, and Run 3 is even better**: This means the combination of dynamic embedding + softplus is highly robust, and dialing back the dropout simply polishes the hydrograph further.