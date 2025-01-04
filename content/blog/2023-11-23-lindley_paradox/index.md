+++
title = "Lindley's Paradox, or The consistency of Bayesian Thinking"
date = "2023-11-22T07:06:59"
author = "Jose Storopoli, PhD"

[taxonomies]
tags = ["math", "bayesian", "probability", "julia"]

[extra]
katex = true
+++

{% admonition(type="warning", icon="tip", title="Evil JavaScript") %}
This post uses [KaTeX](https://katex.org/) to render mathematical expressions.

To see the rendered mathematical expressions, you'll need to enable JavaScript.
{% end %}

![Dennis Lindley](lindley.jpg)

[Dennis Lindley](https://en.wikipedia.org/wiki/Dennis_Lindley),
one of my many heroes,
was an English statistician,
decision theorist and leading advocate of Bayesian statistics.
He published a pivotal book,
[Understanding Uncertainty](https://onlinelibrary.wiley.com/doi/book/10.1002/9781118650158),
that changed my view on what is and how to handle uncertainty in a
coherent way.
He is responsible for one of my favorites quotes:
"Inside every non-Bayesian there is a Bayesian struggling to get out";
and one of my favorite heuristics around prior probabilities:
[Cromwell's Rule](https://en.wikipedia.org/wiki/Cromwell%27s_rule).
Lindley predicted in 1975 that "Bayesian methods will indeed become pervasive,
enabled by the development of powerful computing facilities" (Lindley, 1975).
You can find more about all of Lindley's achievements in his [obituary](https://www.theguardian.com/science/2014/mar/16/dennis-lindley).

## Lindley's Paradox

Lindley's paradox is a counterintuitive situation in statistics
in which the Bayesian and frequentist approaches to a hypothesis testing problem
give different results for certain choices of the prior distribution.

More formally, the paradox is as follows.
We have some parameter $\theta$ that we are interested in.
Then, we proceed with an experiment to test two competing hypotheses:

1. $H_0$ (also known as _null hypothesis_):
   there is no "effect", or, more specifically,
   $\theta = 0$.
1. $H_a$ (also known as _alternative hypothesis_):
   there is an "effect", or, more specifically,
   $\theta \ne 0$.

The paradox occurs when two conditions are met:

1. The result of the experiment is _significant_ by a frequentist test of $H_0$,
   which indicates sufficient evidence to reject $H_0$, at a certain threshold of
   probability.
1. The posterior probability (Bayesian approach) of $H_0 \mid \theta$
   (null hypothesis given $\theta$) is high,
   which indicates strong evidence that $H_0$ should be favored over $H_a$,
   that is, to _not_ reject $H_0$.

These results can occur at the same time when $H_0$ is very specific,
$H_a$ more diffuse,
and the prior distribution does not strongly favor one or the other.
These conditions are pervasive across science
and common in traditional null-hypothesis significance testing approaches.

This is a duel of frequentist versus Bayesian approaches,
and one of the many in which Bayesian emerges as the most coherent.
Let's give a example and go over the analytical result with a ton of math,
but also a computational result with [Julia](https://julialang.org).

## Example

Here's the setup for the example.
In a certain city 49,581 boys and 48,870 girls have been
born over a certain time period.
The observed proportion of male births is thus
$\frac{49,581}{98,451} \approx 0.5036$.

We assume that the birth of a child is independent with a certain probability
$\theta$.
Since our data is a sequence of $n$ independent [Bernoulli trials](https://en.wikipedia.org/wiki/Bernoulli_trial),
i.e., $n$ independent random experiments with exactly two possible outcomes:
"success" and "failure",
in which the probability of success is the same every time the
experiment is conducted.
We can safely assume that it follows a [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution)
with parameters:

- $n$: the number of "trials" (or the total number of births).
- $\theta$: the probability of male births.

We then set up our two competing hypotheses:

1. $H_0$: $\theta = 0.5$.
1. $H_a$: $\theta \ne 0.5$.

### Analytical Solution

This is a toy-problem and, like most toy problems,
we can solve it analytically for both the frequentist and the Bayesian approaches.

#### Analytical Solutions -- Frequentist Approach

The frequentist approach to testing $H_0$ is to compute a $p$-value,
the probability of observing births of boys at least as large as 49,581
assuming $H_0$ is true.
Because the number of births is very large,
we can use a normal approximation for the
binomial-distributed number of male births.
Let's define $X$ as the total number of male births,
then $X$ follows a normal distribution:

$$X \sim \text{Normal}(\mu, \sigma)$$

where $\mu$ is the mean parameter,
$n \theta$ in our case,
and $\sigma$ is the standard deviation parameter,
$\sqrt{n \theta (1 - \theta)}$.
We need to calculate the conditional probability of
$X \geq \frac{49,581}{98,451} \approx 0.5036$
given $\mu = n \theta = 98,451 \cdot \frac{1}{2} = 49,225.5$
and

$\sigma = \sqrt{n \theta (1 - \theta)} =
\sqrt{98,451 \cdot \frac{1}{2} \cdot (1 - \frac{1}{2})}$:

$$P(X \ge 0.5036 \mid \mu = 49,225.5, \sigma = \sqrt{24.612.75})$$

This is basically a
[cumulative distribution function (CDF)](https://en.wikipedia.org/wiki/Cumulative_distribution_function)
of $X$ on the interval $[49,225.5; 98,451]$:

$$
\int_{49,225.5}^{98,451} \frac{1}{\sqrt{2 \pi \sigma^2}}
e^{- \frac{\left( \frac{x - \mu}{\sigma} \right)^2}{2}} dx
$$

After inserting the values and doing some arithmetic,
our answer is approximately $0.0117$.
Note that this is a one-sided test,
since it is symmetrical,
the two-sided test would be
$0.0117 \cdot 2 = 0.0235$.
Since we don't deviate from the Fisher's canon,
this is well below the 5% threshold.
Hooray! We rejected the null hypothesis!
Quick! Grab a frequentist celebratory cigar!
But, wait. Let's check the Bayesian approach.

#### Analytical Solutions -- Bayesian Approach

For the Bayesian approach, we need to set prior probabilities on both hypotheses.
Since we do not favor one from another, let's set equal prior probabilities:

$$P(H_0) = P(H_a) = \frac{1}{2}$$

Additionally, all parameters of interest need a prior distribution.
So, let's put a prior distribution on $\theta$.
We could be fancy here, but let's not.
We'll use a uniform distribution on $[0, 1]$.

We have everything we need to compute the posterior probability of $H_0$ given
$\theta$.
For this, we'll use [Bayes theorem](https://en.wikipedia.org/wiki/Bayes%27_theorem):

$$P(A \mid B) = \frac{P(B \mid A) P(A)}{P(B)}$$

Now again let's plug in all the values:

$$P(H_0 \mid \theta) = \frac{P(\theta \mid H_0) P(H_0)}{P(\theta)}$$

Note that by the [axioms of probability](https://en.wikipedia.org/wiki/Probability_axioms)
and by the [product rule of probability](<https://en.wikipedia.org/wiki/Chain_rule_(probability)>)
we can decompose $P(\theta)$ into:

$$P(\theta) = P(\theta \mid H_0) P(H_0) + P(\theta \mid H_a) P(H_a)$$

Again, we'll use the normal approximation:

$$
\begin{aligned}
  &P \left( \theta = 0.5 \mid \mu = 49,225.5, \sigma = \sqrt{24.612.75} \right) \\\\
  &= \frac{
    \frac{1}{
      \sqrt{2 \pi \sigma^2}
    }
   e^{- \left( \frac{(\mu - \mu \cdot 0.5)}{2 \sigma} \right)^2} \cdot 0.5
  }
  {
    \frac{1}{\sqrt{2 \pi \sigma^2}}
    e^{ \left( -\frac{(\mu - \mu \cdot 0.5)}{2 \sigma} \right)^2} \cdot 0.5 +
    \int_0^1 \frac {1}{\sqrt{2 \pi \sigma^2} }
    e^{- \left( \frac{\mu - \mu \cdot \theta)}{2 \sigma} \right)^2}
    d \theta \cdot 0.5
  } \\\\
  &= 0.9505
\end{aligned}
$$

The likelihood of the alternative hypothesis,
$P(\theta \mid H_a)$,
is just the CDF of all possible values of $\theta \ne 0.5$.

$$
P(H_0 \mid \text{data}) = P \left( \theta = 0.5 \mid \mu = 49,225.5,
sigma = \sqrt{24.612.75} \right) > 0.95
$$

And we fail to reject the null hypothesis, in frequentist terms.
However, we can also say in Bayesian terms, that we strongly favor $H_0$
over $H_a$.

Quick! Grab the Bayesian celebratory cigar!
The null is back on the game!

### Computational Solutional

For the computational solution, we'll use [Julia](https://julialang.org)
and the following packages:

- [`HypothesisTest.jl`](https://github.com/JuliaStats/HypothesisTests.jl)
- [`Turing.jl`](https://turinglang.org/)

#### Computational Solutions -- Frequentist Approach

We can perform a [`BinomialTest`](https://juliastats.org/HypothesisTests.jl/stable/nonparametric/#Binomial-test)
with `HypothesisTest.jl`:

```julia
julia> using HypothesisTests

julia> BinomialTest(49_225, 98_451, 0.5036)
Binomial test
-------------
Population details:
    parameter of interest:   Probability of success
    value under h_0:         0.5036
    point estimate:          0.499995
    95% confidence interval: (0.4969, 0.5031)

Test summary:
    outcome with 95% confidence: reject h_0
    two-sided p-value:           0.0239

Details:
    number of observations: 98451
    number of successes:    49225
```

This is the two-sided test,
and I had to round $49,225.5$ to $49,225$
since `BinomialTest` do not support real numbers.
But the results match with the analytical solution,
we still reject the null.

#### Computational Solutions -- Bayesian Approach

Now, for the Bayesian computational approach,
I'm going to use a generative modeling approach,
and one of my favorites probabilistic programming languages,
`Turing.jl`:

```julia
julia> using Turing

julia> @model function birth_rate()
           θ ~ Uniform(0, 1)
           total_births = 98_451
           male_births ~ Binomial(total_births, θ)
       end;

julia> model = birth_rate() | (; male_births = 49_225);

julia> chain = sample(model, NUTS(1_000, 0.8), MCMCThreads(), 1_000, 4)
Chains MCMC chain (1000×13×4 Array{Float64, 3}):

Iterations        = 1001:1:2000
Number of chains  = 4
Samples per chain = 1000
Wall duration     = 0.2 seconds
Compute duration  = 0.19 seconds
parameters        = θ
internals         = lp, n_steps, is_accept, acceptance_rate, log_density, hamiltonian_energy, hamiltonian_energy_error, max_hamiltonian_energy_error, tree_depth, numerical_error, step_size, nom_step_size

Summary Statistics
  parameters      mean       std      mcse    ess_bulk    ess_tail      rhat   ess_per_sec
      Symbol   Float64   Float64   Float64     Float64     Float64   Float64       Float64

           θ    0.4999    0.0016    0.0000   1422.2028   2198.1987    1.0057     7368.9267

Quantiles
  parameters      2.5%     25.0%     50.0%     75.0%     97.5%
      Symbol   Float64   Float64   Float64   Float64   Float64

           θ    0.4969    0.4988    0.4999    0.5011    0.5031
```

We can see from the output of the quantiles that the 95% quantile for $\theta$ is
the interval $(0.4969, 0.5031)$.
Although it overlaps zero, that is not the equivalent of a hypothesis test.
For that, we'll use the
[highest posterior density interval (HPDI)](https://en.wikipedia.org/wiki/highest_posterior_density_interval),
which is defined as "choosing the narrowest interval" that
captures a certain posterior density threshold value.
In this case, we'll use a threshold interval of 95%,
i.e. an $\alpha = 0.05$:

```julia
julia> hpd(chain; alpha=0.05)
HPD
  parameters     lower     upper
      Symbol   Float64   Float64

           θ    0.4970    0.5031
```

We see that we fail to reject the null,
$\theta = 0.5$ at $\alpha = 0.05$ which is in accordance with the analytical
solution.

## Why the Frequentist and Bayesian Approaches Disagree

Why do the approaches disagree?
What is going on under the hood?

The answer is disappointing.
The main problem is that the frequentist approach only allows fixed significance
levels with respect to sample size.
Whereas the Bayesian approach is consistent and robust to sample size variations.

Taken to extreme, in some cases, due to huge sample sizes,
the $p$-value is pretty much a _proxy_ for sample size
and have little to no utility on hypothesis testing.
This is known as $p$-hacking.

## References

{% references() %}

Lindley, Dennis V. "The future of statistics: A Bayesian 21st century".
_Advances in Applied Probability_ 7 (1975): 106-115.

{% end %}
