---
title: "Randomness in computation: sprinkle a little bit of randomness, and voilà!"
date: 2025-04-07
author: Jose Storopoli
description: How to make your own non-deterministic, but highly reliable, linear
tags: [math, probability, programming, haskell]
---

![Just sprinkle a little bit of randomness, and voilà!](/images/randomness-meme.jpg)

Sometimes when you deal with complicated computations,
either because of the input size or the complexity of the computation,
you cannot get an answer in any feasible amount of time,
no matter how much computational power you have.

When the limits of tractability are reached,
we can give up deterministic computation and embrace **randomness**
to get an answer in a much more reasonable time.

This is the case of [Monte Carlo methods](https://en.wikipedia.org/wiki/Monte_Carlo_method),
which are a class of algorithms that use **random sampling**
to solve mathematical problems.
And, of course, like everything nice in math and computer science,
it has the **Von Neumann's fingerprints** all over it.
Alas, that is a story for another post, that I already covered in
["Von Neumann: the Sharpest Mind of the 20th Century"](/posts/2024-06-22-von-neumann.html).

I was recently skimming over a textbook that I used to use
in my undergraduate course on probability theory [@probabilitycomputing][^pdf],
and I stumbled upon a very interesting algorithm for calculating the **median** of a list.

By the way, this textbook has one of the **best covers** in math textbooks.
It is Alice in Wonderland dealing with a combinatorial explosion,
see it below:

![Probability and Computing: Randomization and Probabilistic Techniques in Algorithms and Data Analysis 2nd Edition](/images/probability-and-computing.jpg)

[^pdf]: {-} The PDF is freely available [here](http://lib.ysu.am/open_books/413311.pdf).

The algorithm uses sampling to probabilistically find the **median**,
and uses [Chebyshev's inequality](https://en.wikipedia.org/wiki/Chebyshev's_inequality),
an upper bound on the probability of deviation of a random variable from its mean.
Since it is a probabilistic algorithm,
it finds the median in $O(n)$ (linear time) with probability
$1 - n^{-\frac{1}{4}}$ (close to $1$ for large $n$).
Note that for any deterministic algorithm to find the median,
it needs to sort the list, which takes $O(n \log n)$ (linearithmic time)
on average or $O(n^2)$ (quadratic time) in the worst case[^quicksort].
You can always iterate and run the algorithm until you get a result,
but now the runtime is **non-deterministic**.

[^quicksort]:
    {-} Note that I am comparing against quicksort since it uses $O(\log n)$ space,
    whereas merge sort would use $O(n)$ space with the worst case is $O(n)$.

The nice thing about the algorithm is that Chebyshev's inequality
does not makes assumptions about the distribution of the variable,
just that it has a **finite variance**.
This is excellent since we can move away from the **lala-land** of
normal distributions assumptions that everything is a Gaussian bell curve[^bayesian].

[^bayesian]:
    {-} For my Bayesian rant,
    see ["Lindley's Paradox, or The consistency of Bayesian Thinking"](/posts/2023-11-23-lindley_paradox.html).

## Chebyshev's Inequality

Chebyshev's inequality provides an upper bound on the probability
of deviation of a random variable (with finite variance) from its mean.

The inequality is given by:

$$
P(|X - \mu| \geq k \sigma) \leq \frac{1}{k^2}
$$

where $X$ is a random variable, $\mu$ is the mean,
$\sigma$ is the standard deviation, and $k$ is a positive real number.

This is a consequence of the [Markov's inequality](https://en.wikipedia.org/wiki/Markov's_inequality),
and can be derived using simple algebra.
The reader that is interested in the proof or more details,
see the Wikipedia pages linked above.

Because Chebyshev's inequality can be applied to any distribution with finite mean and variance,
it generally gives **looser bounds** compared to what we might get if we knew more about the specific distribution.
Here's a table showing how much of the distribution's values must lie within $k$ standard deviations of the mean:

| $k$        | Min. % within $k$ standard deviations | Max. % beyond $k$ standard deviations |
|------------|---------------------------------------|---------------------------------------|
| 1          | 0%                                    | 100%                                  |
| $\sqrt{2}$ | 50%                                   | 50%                                   |
| 2          | 75%                                   | 25%                                   |
| 3          | 88.8889%                              | 11.1111%                              |
| 4          | 93.75%                                | 6.25%                                 |
| 5          | 96%                                   | 4%                                    |
| 10         | 99%                                   | 1%                                    |

For example, while we know that for a normal distribution about 68% of values lie within one standard deviation,
Chebyshev only tells us that **at least** 0% must lie within one standard deviation!
This is the price we pay for having a bound that works on any distribution.
Yet, it is still a **very useful bound**.

## Randomized Median

Alright, now let's see in practice how this works.
Below is the algorithm for finding the median of a list,
as described in algorithm 3.1 in the "Probability and Computing" textbook:

**Input:** A set $S$ of $n$ elements over a totally ordered universe.

**Output:** The median element of $S$, denoted by $m$.

1. Pick a (multi-)set $R$ of $\lceil n^{\frac{3}{4}} \rceil$ elements in $S$, chosen independently and uniformly at random with replacement.
2. Sort the set $R$.
3. Let $d$ be the $\bigg(\left\lfloor \frac{1}{2}n^{\frac{3}{4}} - \sqrt{n} \right\rfloor\bigg)$th smallest element in the sorted set $R$.
4. Let $u$ be the $\bigg(\left\lceil \frac{1}{2}n^{\frac{3}{4}} + \sqrt{n} \right\rceil\bigg)$th smallest element in the sorted set $R$.
5. By comparing every element in $S$ to $d$ and $u$, compute the set $C = \big\{x \in S : d \leq x \leq u \big\}$ and the numbers $\ell_d = \bigg| \big\{x \in S : x < d \big\}\bigg|$ and $\ell_u = \bigg| \big\{x \in S : x > u \big\}\bigg|$.
6. If $\ell_d > n/2$ or $\ell_u > n/2$ then FAIL.
7. If $\big|C\big| \leq 4n^{\frac{3}{4}}$ then sort the set $C$, otherwise FAIL.
8. Output the $\big(\lfloor \frac{n}{2} \rfloor - \ell_d + 1\big)$th element in the sorted order of $C$.

As you can see, the algorithm starts by sampling a set of elements from the list,
sorting them, and then using the sorted elements to find the median.
How it finds the median is by using the set $C$,
which is the set of elements in $S$ that are between $d$ and $u$,
where $d$ is the lower bound and $u$ is the upper bound of the
sampled set $R$.

The algorithm's brilliance lies in its **probabilistic guarantees**.
It can fail in three ways:

1. Too few sampled elements are less than the true median
2. Too few sampled elements are greater than the true median
3. The set $C$ becomes too large to sort efficiently

However, the probability of any of these failures occurring is **remarkably small**: less than $n^{-\frac{1}{4}}$.
This means that as the input size grows, the chance of failure becomes increasingly negligible:

- For n = 10,000: failure probability ≤ 0.1
- For n = 1,000,000: failure probability ≤ 0.032
- For n = 100,000,000: failure probability ≤ 0.01

When the algorithm doesn't fail (which is the vast majority of the time),
it is guaranteed to find the **exact median** in linear time.
This is achieved by carefully choosing the sample size, $n^{\frac{3}{4}}$, and
the buffer zone around the median, $\sqrt{n}$, to balance between:

1. Having enough samples to make failure unlikely
2. Keeping the set $C$ small enough to sort quickly

The algorithm provides two important guarantees:

1. **Correctness**: The algorithm is guaranteed to either FAIL or return the true median.
   This is proven using Chebyshev's inequality in two steps.
   First, we show that the true median $m$ will be in set $C$ with high probability:

   - Let $Y_1$ be the count of sampled elements ≤ $m$ in $R$
     - When $Y_1 < \frac{1}{2}n^{\frac{3}{4}} - \sqrt{n}$, we call this event $\mathcal{E}_1$
   - Let $Y_2$ be the count of sampled elements ≥ $m$ in $R$
     - When $Y_2 < \frac{1}{2}n^{\frac{3}{4}} - \sqrt{n}$, we call this event $\mathcal{E}_2$
   - When $|C| > 4n^{\frac{3}{4}}$, we call this event $\mathcal{E}_3$
   - By Chebyshev's inequality, each event has probability at most $\frac{1}{4}n^{-\frac{1}{4}}$

   Second, we show that when $m$ is in $C$, we find it:

   - $\ell_d$ counts elements < $d$, so there are exactly $\big\lfloor \frac{n}{2} \big\rfloor - \ell_d$ elements between $d$ and $m$
   - Therefore, $m$ must be the $\bigg(\big\lfloor \frac{n}{2} \big\rfloor - \ell_d + 1\bigg)$th element in the sorted $C$

1. **Linear Time**: The algorithm runs in $O(n)$ time when it succeeds because:

   - Sampling and sorting $R$ takes $O\left(n^\frac{3}{4} \log n\right)$ time
   - Comparing all elements to $d$ and $u$ takes $O(n)$ time
   - Sorting $C$ takes $O\left(n^\frac{3}{4} \log n\right)$ time since $|C| \leq 4n^\frac{3}{4}$
   - All other operations are constant time

### Why These Guarantees Work

The key to understanding why this algorithm works lies in analyzing the **probability of failure**.
Let's look at how we bound the probability of having too few samples below the median (event $\mathcal{E}_1$):

1. For each sampled element $i$, define an indicator variable $X_i$ where:
   $$
   X_i = 1 \text{ if the $i$th sample is } \leq \text{ median}
   $$
   $$
   X_i = 0 \text{ otherwise}
   $$

1. Since we sample with replacement, the $X_i$ are independent. And since there are
   $\frac{n-1}{2} + 1$ elements ≤ median in $S$, we have:
   $$
   P(X_i = 1) = \frac{\frac{n-1}{2} + 1}{n} = \frac{1}{2} + \frac{1}{2n}
   $$

1. Let $Y_1 = \sum_{i=1}^{n^{3/4}} X_i$ count samples ≤ median. This is a binomial random variable with:

   - Expected value: $E[Y_1] = n^{\frac{3}{4}}\left(\frac{1}{2} + \frac{1}{2n}\right)$
   - Variance: $Var[Y_1] < \frac{1}{4}n^{\frac{3}{4}}$

1. Using Chebyshev's inequality:
   $$
   P \left(Y_1 < \frac{1}{2}n^{\frac{3}{4}} - \sqrt{n} \right) \leq \frac{Var[Y_1]}{n} < \frac{1}{4}n^{-\frac{1}{4}}
   $$

This shows that both events $\mathcal{E}_1$ and $\mathcal{E}_2$ have probability at most $\frac{1}{4}n^{-\frac{1}{4}}$,
and also that $\mathcal{E}_3$ has probability at most $\frac{1}{4}n^{-\frac{1}{4}}$:

$$
P(\mathcal{E}_1) \leq P(\mathcal{E}_2 + \mathcal{E}_3) \leq \frac{1}{2}n^{-\frac{1}{4}}
$$

All these events combined demonstrate that the algorithm rarely fails: the probability of having too few samples
on either side of the median decreases as $n^{-\frac{1}{4}}$, becoming negligible for large $n$.
If higher reliability is needed, you can simply run the algorithm multiple times,
as each run is independent.

## Haskell Implementation

I implemented the algorithm in **Haskell**,
because I stare at **Rust** code 8+ hours a day,
and I want programming in a language that
"if it compiles, it is guaranteed to run".
The only other language apart from Rust that has this property,
and some might say that it is the only language that has this property,
is Haskell.

The code can be found on GitHub at [`storopoli/randomized-median`](https://github.com/storopoli/randomized-median).

So let's first go over the vanilla, classical, deterministic median algorithm:

```haskell
median :: (Ord a, Fractional a) => [a] -> Maybe a
median [] = Nothing
median xs =
  -- First convert list to array for O(1) random access
  let n = length xs
      arr = listArray (0, n - 1) xs
      -- Sort the array elements
      sorted = sort (elems arr)
      sortedArr = listArray (0, n - 1) sorted
      mid = n `div` 2
   in if odd n
        then Just (sortedArr ! mid)
        else Just ((sortedArr ! (mid - 1) + sortedArr ! mid) / 2)
```

First we define a function signature for the median function:
it takes a list or elements of some type that is an instance of both the `Ord` type class,
and the `Fractional` type class.
This is because we must assure the Haskell compiler that the elements of the list can be
ordered and that we can perform fractional arithmetic on them.
It returns a `Maybe a` because the median is not defined for empty lists.
The `Maybe` type is an instance of the `Monad`[^monad] type class,
which allows us to use the `>>=` operator to chain computations that may fail.
It can take two values `Nothing` or `Just a`, where `a` is the type of the elements of the list.

[^monad]:
    {-} Yes M word mentioned.
    If you want a good introduction to Haskell functors, applicatives, and monads,
    see ["Functors, Applicatives, And Monads In Pictures"](https://www.adit.io/posts/2013-04-17-functors,_applicatives,_and_monads_in_pictures.html)

For the case of an empty list, we return `Nothing`.
For the case of a non-empty list, we convert the list to an array,
sort the array, and then find the median,
returning the median as a `Just` value.

Now, let's implement the randomized median algorithm:

```haskell
randomizedMedian :: (Ord a) => [a] -> Int -> Maybe a
randomizedMedian [] _ = Nothing
randomizedMedian xs seed =
  let n = length xs
      arr = listArray (0, n - 1) xs

      -- Step 1: Sample n^(3/4) elements with replacement
      sampleSize = ceiling (fromIntegral n ** (3 / 4))
      gen = mkStdGen seed
      indices = take sampleSize $ randomRs (0, n - 1) gen

      -- Step 2: Sort the sample
      sample = sort [arr ! i | i <- indices]
      sampleArr = listArray (0, length sample - 1) sample

      -- Step 3: Find d (the lower bound element)
      dIndex = floor (fromIntegral n ** (3 / 4) / 2 - sqrt (fromIntegral n))
      d =
        if dIndex >= 0 && dIndex < length sample
          then sampleArr ! dIndex
          else error "Invalid d index"

      -- Step 4: Find u (the upper bound element)
      uIndex = floor (fromIntegral n ** (3 / 4) / 2 + sqrt (fromIntegral n))
      u =
        if uIndex >= 0 && uIndex < length sample
          then sampleArr ! uIndex
          else error "Invalid u index"

      -- Step 5: Compute set C and counts
      ld = length $ filter (< d) xs
      lu = length $ filter (> u) xs
      c = sort $ filter (\x -> d <= x && x <= u) xs

      -- Step 6 & 7: Check failure conditions
      halfN = n `div` 2
   in ( if ((ld > halfN || lu > halfN) || (length c > 4 * sampleSize)) || null c
          then Nothing
          else
            ( let targetIndex = halfN - ld
               in if targetIndex >= 0 && targetIndex < length c
                    then
                      -- Step 8: Output the median
                      Just (c !! targetIndex)
                    else
                      Nothing
            )
      )
```

I've added comments to the code with respect to the algorithm steps.
First, the function signature is almost the same as the deterministic median function.
There are two differences:

1. The elements of the list does not need to be a `Fractional` type.
1. We now take an additional parameter, `seed`,
   which is the seed for the random number generator.
   This is needed since we are using a random number generator to sample the elements from the list.

As before, for the case of an empty list, we return `Nothing`.

For the case of a non-empty list, we first convert the list to an array,
and then sample `n^(3/4)` elements from the list with replacement.
We use the [`randomRs`](https://hackage.haskell.org/package/random-1.1/docs/System-Random.html#v:randomR)
function to generate a list of random indices,
it generates an infinite list of random values within the specified range
(in this case, from `0 to n-1`),
hence sampling with replacement.
Then, we take the first `n^(3/4)` elements from the list.
Next, we sort the sample and convert it to an array.

Next, we find the lower and upper bounds of the sample.
We do this by finding the index of the element at position `n^(3/4)/2 - sqrt(n)`
and `n^(3/4)/2 + sqrt(n)` in the sorted sample.
We then take the element at these indices as the lower and upper bounds.

Then, we compute the set $C$ and the counts $\ell_d$ and $\ell_u$.
We do this by filtering the list with the lower and upper bounds.

Next, we check if the set $C$ is too large to sort efficiently.
If it is, we return `Nothing`.
Otherwise, we sort the set $C$ and find the median.

## Results

Here's the result by running the algorithm against a randomly shuffled list of contiguous integers from 1 to 10,000,001
using the **magical number 42** as the seed of our random number generator.
As you can see both the exact and randomized median algorithms find the right
median value:

$$ \frac{10,000,001}{2} = 5,000,001 $$

since $10,000,001$ is odd, the median is the element at position $\frac{10,000,001}{2} = 5,000,001$.

```bash
============================
Testing with 10_000_001 shuffled elements

Exact median calculation:
  Result: 5000001.0
  Time: 18.906611 seconds

Randomized approximate median calculation:
  Result: 5000001.0
  Time: 1.095511 seconds

Error percentage: 0.0000%
Speedup factor: 17.26x
```

The randomized median algorithm for the case of $n = 10,000,001$
is at least **17x faster** than the exact median calculation.
That is an **order of magnitude improvement** over the deterministic median algorithm.

## Conclusion

I love the inequalities of the **Russian school of probability**,
Markov, Chebyshev, etc.,
since it does not depend on any underlying distributional assumptions.
Chebyshev's inequality depends on the random variable having a finite mean and variance,
and Markov's inequality depends on the random variable being non-negative but does not depend on finite variances.

Assuming that the underlying variable has finite variance is a reasonable assumption to make
most of the time for your data.
To be fair, there are some random variables that can have infinite variance,
such as the [Cauchy](https://en.wikipedia.org/wiki/Cauchy_distribution)
or [Pareto](https://en.wikipedia.org/wiki/Pareto_distribution) distributions,
but these are **extremely rare** for you to cross paths with.

Another thing to note is that instead of the Chebyshev's inequality,
we could have used the [Chernoff bound](https://en.wikipedia.org/wiki/Chernoff_bound)
to get a **tighter bound** on the probability of failure.
But that is "left as an exercise to the reader".

Finally, if you are intrigued to see how powerful these inequalities
can be in probability theory,
I highly recommend Nassim's Taleb technical book
"Statistical Consequences of Fat Tails: Real World Preasymptotics, Epistemology, and Applications" [@taleb2022statisticalconsequencesfattails]
which is freely available on arXiv.
