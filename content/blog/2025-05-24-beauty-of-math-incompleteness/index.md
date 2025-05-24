+++
title = "The beauty of math's incompleteness or how self-references can beautifully screw things up"
date = "2025-05-24T12:57:00"
author = "Jose Storopoli, PhD"

[taxonomies]
tags = ["math", "programming", "agda"]

[extra]
katex = true
+++

{{ katex() }}

![A curios mathematician seeing a blackhole of self-referential paradoxes.](self-referential-blackhole.png)

I have a very special place for mathematics in my mind and heart.

Mathematics is above any other science.
This is because the knowledge we gather in all other sciences are never absolute true.
All other sciences are based on observations and experiments,
and eventually evidence accrues to a threshold that we can morally declare that something is true.
Yet, it is not mathematically true, in other words, for any given pile of evidence about a given hypothesis $H$,
we have $P(H) < 1$.
In a pure philosophical sense, we can never be absolutely sure about scientific hypotheses.
There will always be a certain degree of uncertainty even if we have a lot of evidence in favor of a given hypothesis.
For mathematical theorems, which is the meat of mathematics, once they are proven, they are absolute true,
i.e. $P(H) = 1$.
For example, imagine a galaxy very far away, and a million years from now, given the
[5 axioms of Euclidian geometry](https://en.wikipedia.org/wiki/Euclidean_geometry#Axioms),
the theorem that the sum of the angles of a triangle is 180 degrees will still be true.
It will always be true (given the 5 axioms of course).

That is how mathematics won my mind.
Now, how it won my heart is a different story.
It has to do with the beauty of math's incompleteness.
And this is what I want to talk about in this post,
along with some contextual history and some theorem proving in [Agda](https://agda.readthedocs.io/).

## Cantor and multiple infinities

![Georg Cantor](georg-cantor.jpg)

Let's go back to 1874, when [Georg Cantor](https://en.wikipedia.org/wiki/Georg_Cantor)
proved that there are multiple infinities.
Yes, that sounds crazy, but it is true.

Cantor is the father of set theory.
Before him, the concept of a set was just a collection of objects and they were all finite collections.
This dates back to Aristotle, and no one imagined that there was interesting things to say about sets.
In order to put set theory on a solid footing, Cantor had to define what a set is.
For finite sets, this was kinda trivial.
However, for infinite sets, this is where things started to get interesting.

Cantor started exploring the properties of infinite sets.
First, he analyzed the properties of the set of natural numbers $\mathbb{N}$.
He then realized that the set of natural numbers is the same size
as the set of the integers $\mathbb{Z}$ and the set of the rational numbers $\mathbb{Q}$.
To show this, he had to come up with a way to compare the sizes of sets.
He did this by defining a bijection between the set of natural numbers and the set of integers.
A bijection is a function that is one-to-one and onto.
In other words, it is a function that maps each element of the first set to a unique element of the second set,
and each element of the second set to a unique element of the first set.

For example, the function

$$
f(n) = \begin{cases}
    -\frac{n}{2} & \text{if } n \text{ is even} \\\\
    \frac{n+1}{2} & \text{if } n \text{ is odd}
\end{cases}
$$

is a bijection between the set of natural numbers and the set of integers.

It creates a one-to-one correspondence between the set of natural numbers and the set of integers:

| $f(n)$ | $\mathbb{N}$ | $\mathbb{Z}$ |
|--------|--------------|--------------|
| f(0)   | 0            | 0            |
| f(1)   | 1            | 1            |
| f(2)   | 2            | -1           |
| f(3)   | 3            | 2            |
| f(4)   | 4            | -2           |
| f(5)   | 5            | 3            |
| f(6)   | 6            | -3           |

Ok that was easy, we just proved that the set of natural numbers and the set of integers have the same size.
Now let's try to prove the same for the set of rational numbers $\mathbb{Q}$.
The idea again is to find a bijection between the set of natural numbers and the set of rational numbers.
We can represent the set of rational numbers as a grid of fractions:

$$
\begin{array}{cccc}
    \frac{1}{1} & \quad \frac{1}{2} & \quad \frac{1}{3} & \quad \cdots \\\\\\\\
    \frac{2}{1} & \quad \frac{2}{2} & \quad \frac{2}{3} & \quad \cdots \\\\\\\\
    \frac{3}{1} & \quad \frac{3}{2} & \quad \frac{3}{3} & \quad \cdots \\\\\\\\
    \vdots & \quad \vdots & \quad \vdots & \quad \ddots \\\\\\\\
\end{array}
$$

Now, we can't just go row by row or column by column - that would never finish the first row!
Instead, Cantor had a brilliant idea: traverse the grid diagonally in a zigzag pattern[^pairing-function].

[^pairing-function]: This is called a [pairing function](https://en.wikipedia.org/wiki/Pairing_function), and specifically the [Cantor pairing function](https://en.wikipedia.org/wiki/Cantor_pairing_function).

$$
\begin{array}{ccccc}
    \frac{1}{1} & \rightarrow & \frac{1}{2} & \quad & \frac{1}{3} & \rightarrow & \frac{1}{4} & \cdots \\\\
    & \swarrow & & \nearrow & & \swarrow & \\\\
    \frac{2}{1} & & \frac{2}{2} & & \frac{2}{3} & & \frac{2}{4} & \cdots \\\\
    \downarrow & \nearrow & & \swarrow & & & \\\\
    \frac{3}{1} & & \frac{3}{2} & & \frac{3}{3} & & \frac{3}{4} & \cdots \\\\
    & \swarrow & & \nearrow & & & \\\\
    \frac{4}{1} & & \frac{4}{2} & & \frac{4}{3} & & \frac{4}{4} & \cdots \\\\
    \vdots & & \vdots & & \vdots & & \vdots & \ddots \\\\
\end{array}
$$

This gives us the sequence:
$$
\frac{1}{1}, \frac{1}{2}, \frac{2}{1}, \frac{3}{1}, \frac{2}{2}, \frac{1}{3}, \frac{1}{4}, \frac{2}{3}, \frac{3}{2}, \frac{4}{1}, \ldots
$$

But wait! We have a problem --- many fractions represent the same rational number:
- $\frac{2}{2} = \frac{1}{1} = 1$
- $\frac{2}{4} = \frac{1}{2} = 0.5$

To create a true bijection, we need to skip these duplicates.
 We only keep fractions in **lowest terms**,
 where $\text{gcd}(\text{numerator}, \text{denominator}) = 1$.

After removing duplicates:
$$\frac{1}{1}, \frac{1}{2}, \frac{2}{1}, \frac{3}{1}, \frac{1}{3}, \frac{1}{4}, \frac{2}{3}, \frac{3}{2}, \frac{4}{1}, \ldots$$

Ok we're almost there. This is truly a bijection.
However, it is a bijection between $\mathbb{N}$ and the set of positive rationals $\mathbb{Q}^+$.
To include all of $\mathbb{Q}$, we interleave positive and negative rationals (and zero).
I won't give the precise mathematical formula here because it is a bit messy,
however here's an algorithm describing the bijection:

1. Start with $n$
2. If $n = 0$, return $0$
3. Otherwise:
   - Let $k = \frac{n+1}{2}$ if $n$ is odd, $k = \frac{n}{2}$ if $n$ is even
   - Find the $k$-th positive rational in our enumeration, call it $r$
   - If $n$ is odd, return $r$
   - If $n$ is even, return $-r$

This gives us the following bijection:

| $g(n)$ | $\mathbb{N}$ | $\mathbb{Q}^+$ enumeration  | $\mathbb{Q}$   |
|--------|--------------|-----------------------------|----------------|
| g(0)   | 0            | -                           | 0              |
| g(1)   | 1            | 1st positive: $\frac{1}{1}$ | 1              |
| g(2)   | 2            | 1st positive: $\frac{1}{1}$ | -1             |
| g(3)   | 3            | 2nd positive: $\frac{1}{2}$ | $\frac{1}{2}$  |
| g(4)   | 4            | 2nd positive: $\frac{1}{2}$ | $-\frac{1}{2}$ |
| g(5)   | 5            | 3rd positive: $\frac{2}{1}$ | 2              |
| g(6)   | 6            | 3rd positive: $\frac{2}{1}$ | -2             |

Q.E.D.! We have a bijection between $\mathbb{N}$ and $\mathbb{Q}$.

I went over all of these details because this diagonalization argument is a very important insight.
Any set that can be put in a one-to-one correspondence with the set of natural numbers is called countable.
Cantor showed that the set of rational numbers is countable.

Let's see what happens when we try to apply the same argument to the set of real numbers $\mathbb{R}$.
For the sake of simplicity, let's consider the set of real numbers between 0 and 1, $\mathbb{R}_{(0,1)}$.
Let's assume that we have a bijection $f$ between $\mathbb{N}$ and $\mathbb{R}_{(0,1)}$.
This would give us the following table:

| $f(n)$ | $\mathbb{N}$ | $\mathbb{R}_{(0,1)}$ |
|--------|--------------|----------------------|
| f(0)   | 0            | 0.011...             |
| f(1)   | 1            | 0.111...             |
| f(2)   | 2            | 0.112...             |
| ...    | ...          | ...                  |

Note that the real number $f(n)$ is the $n$-th real number in the list.

Now, let's construct a new real number $x$ that is not in the list.
We will do this by constructing a real number that is different from the $n$-th real number in the list for all $n$.
We just add 1 to the $n$-th digit of the $n$-th real number in the list.
For example, for the first real number in the list, we add 1 to the first digit,
for the second real number in the list, we add 1 to the second digit,
and so on.

This gives us the following real number: $0.123\ldots$
By construction, this real number is not in the list,
since it differs from the first real number in the list by 1 in the first digit,
from the second real number in the list by 1 in the second digit,
and so on.

This is a contradiction, since we assumed that $f$ was a bijection.

Now, this is where self-reference strikes first in this post,
and probably in the history of mathematics.
When we construct the diagonal number $x$, we're creating something that:

1. Refers to the entire supposed list of real numbers.
2. Defines itself in opposition to that list - "I differ from the 1st number at position 1, from the 2nd at position 2...".
3. Uses the list to prove the list is incomplete.

Ultimately, this is where Cantor found the first example of a set that is not countable.
There's no way to pair the set of natural numbers with the set of real numbers between 0 and 1.
Therefore, the set of real numbers between 0 and 1 is not countable.

This is a very important insight.
It shows that there are different sizes of infinity.
Yes, that is mind-blowing and paradoxically beautiful.

Cantor called the size of the set of natural numbers $\aleph_0$,
and conjectured that the set of real numbers is $\aleph_1$.
This is called the [continuum hypothesis](https://en.wikipedia.org/wiki/Continuum_hypothesis) (CH).
We will come back to CH later.

## Russel and the barber paradox

![Bertrand Russell](bertrand-russell.jpg)

Now let's fast forward to 1901.
Set theory was still in its infancy,
yet it was starting to be accepted by the mathematical community.
This is where [Bertrand Russell](https://en.wikipedia.org/wiki/Bertrand_Russell)
after attending the first [World Congress of Philosophy](https://en.wikipedia.org/wiki/World_Congress_of_Philosophy) in Paris in 1900,
was impressed by the work of Peano who was using set theory to formalize mathematics.

He embarked on a journey to formalize mathematics using set theory.
However, he stumbled upon a paradox.
Set theory is very lenient with the definition of sets.
For example, we can define the set of all sets that are not members of themselves:

$$
R = \\{ x \mid x \notin x \\}
$$

Now what happens if we ask the question: is $R$ a member of itself?
If $R$ is a member of itself, then it is not a member of itself.
If $R$ is not a member of itself, then it is a member of itself.

To put more simply, Russell gave the simple analogy:
imagine a barber who shaves all men who do not shave themselves.
Now, the question is: does the barber shave himself?
If he does, then he does not shave himself.
If he does not shave himself, then he does shave himself.

I can even given an even more simple example: the statement "this statement is false" is a paradox.
If it is true, then it is false.
If it is false, then it is true.

Or suppose that I go out and shout out loud: "I am lying".
If I am lying, then I am not lying.
If I am not lying, then I am lying.

All of these examples boils down to the same thing:
we cannot have a set of all sets that are not members of themselves.

This is called the [Russell's paradox](https://en.wikipedia.org/wiki/Russell%27s_paradox).
And yet again, we have self-reference creating a paradox.
Personally, I find Cantor's multiple infinities more beautiful than Russell's paradox.
But I acknowledge that Russell's paradox is way simpler and more accessible to the general public.


## Scratch pad

Gödel (1940): Proved that CH cannot be disproved from the standard axioms of set theory (ZFC)
Cohen (1963): Proved that CH cannot be proved from ZFC either

