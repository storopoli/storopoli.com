+++
title = "Randomness in Computation: Sprinkle a little bit of randomness, and voilà!"
date = "2025-04-07T06:57:00"
author = "Jose Storopoli, PhD"

[taxonomies]
tags = ["math", "probability", "programming", "haskell"]

[extra]
katex = true
+++

{% admonition(type="warning", icon="warning", title="Evil JavaScript") %}
This post uses [KaTeX](https://katex.org/) to render mathematical expressions.

To see the rendered mathematical expressions, you'll need to enable JavaScript.
{% end %}

TODO: Nice Image.

Sometimes when you deal with complicated computations,
either because of the input size or the complexity of the computation,
you cannot get an answer in any feasible amount of time,
no matter how much computational power you have.

When the limits of tractability are reached,
we can give up deterministic computation and embrace randomness
to get an answer in a much more reasonable time.

This is the case of Monte Carlo methods,
which are a class of algorithms that use random sampling
to solve mathematical problems.
And, of course, like everything nice in math and computer science,
it has the Von Neumann's fingerprints all over it.
Alas, that is a story for another post, that I already covered in
["Von Neumann: the Sharpest Mind of the 20th Century"](@/blog/2024-06-22-von-neumann/index.md).

I was recently skimming over a textbook that I used to use
in my undergraduate course on probability theory (Mitzenmacher and Upfal's
"Probability and Computing"[^pdf], see references below),
and I stumbled upon a very interesting algorithm for calculating the median of a list.

[^pdf]: The PDF is freely available [here](http://lib.ysu.am/open_books/413311.pdf).

The algorithm is based on the Chernoff bound,
which is an inquality ...

## Chernoff Bound

## Randomized Median

**Input:** A set $S$ of $n$ elements over a totally ordered universe.

**Output:** The median element of $S$, denoted by $m$.

1. Pick a (multi-)set $R$ of $\lceil n^{3/4} \rceil$ elements in $S$, chosen independently and uniformly at random with replacement.
2. Sort the set $R$.
3. Let $d$ be the $\left(\left\lfloor \frac{1}{2}n^{3/4} - \sqrt{n} \right\rfloor\right)$th smallest element in the sorted set $R$.
4. Let $u$ be the $\left(\left\lfloor \frac{1}{2}n^{3/4} + \sqrt{n} \right\rfloor\right)$th smallest element in the sorted set $R$.
5. By comparing every element in $S$ to $d$ and $u$, compute the set $C = \\{x \in S : d \leq x \leq u\\}$ and the numbers $\ell_d = |\\{x \in S : x < d\\}|$ and $\ell_u = |\\{x \in S : x > u\\}|$.
6. If $\ell_d > n/2$ or $\ell_u > n/2$ then FAIL.
7. If $|C| \leq 4n^{3/4}$ then sort the set $C$, otherwise FAIL.
8. Output the $(\lfloor n/2 \rfloor - \ell_d + 1)$th element in the sorted order of $C$.

## Haskell Implementation

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

## Results

```bash
============================
Testing with 10_000_000 shuffled elements

Exact median calculation:
  Result: 5000000.5
  Time: 18.906611 seconds

Randomized approximate median calculation:
  Result: 5000001.0
  Time: 1.095511 seconds

Error percentage: 0.0000%
Speedup factor: 17.26x
```

## Conclusion

...

## References

- Michael Mitzenmacher and Eli Upfal, "Probability and Computing: Randomization and Probabilistic Techniques in Algorithms and Data Analysis 2nd Edition", ISBN: 978-1107154889