---
title: Shamir's secret sharing
date: 2024-04-14
author: Jose Storopoli
description: How to share secrets and do threshold cryptography.
tags: [math, cryptography, bitcoin]
---

![The Polynomial king and he can do anything!](/images/polynomial_king.webp)

In this post, we'll talk about
**[Shamir's Secret Sharing](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing)
(SSS)**, a cryptographic algorithm that allows us to **split a secret into multiple parts,
called shares, in such a way that the secret can only be reconstructed
if a certain number of shares are combined**.

The idea is to give a visual intuition of how the algorithm works,
and describe the mathematical details behind it.

The code for all the plots in this post can be found in
[`storopoli/shamir-secret-sharing`](https://github.com/storopoli/shamir-secret-sharing).

## Polynomial Interpolation

**If you have two points you can draw a _unique_ line that passes through them**.
Suppose that you have the points $(3,3)$ and $(4,4)$.
Hence, there is only one line that passes through these two points.
See the plot below.

![A line passing through two points](/images/shamir-line.svg)

**If you have three points you can draw a _unique_ parabola that passes through them**.
Suppose that you have the points $(-4,16)$, $(1,1)$, and $(4,16)$.
Hence, there is only one parabola that passes through these three points.

![A parabola passing through three points](/images/shamir-quadratic.svg)

**If you have four points you can draw a _unique_ cubic polynomial that passes through them**.
Suppose that you have the points $(-2,8)$, $(-1,1)$, $(1,1)$, and $(2,8)$.
Hence, there is only one cubic polynomial that passes through these four points.

![A cubic polynomial passing through four points](/images/shamir-cubic.svg)

As you might have guessed, **if you have $n$ points you can draw a _unique_ polynomial of degree $n-1$ that passes through them**.
This is called **polynomial interpolation**[^interpolation].

[^interpolation]: Steams from the [Lagrange interpolation](https://en.wikipedia.org/wiki/Lagrange_polynomial).

More formally, say that we have a polynomial $f(x)$ of degree $n$:

$$ f(x) = ax^n + a\_{n-1} x^{n-1} + \ldots + a_1 x + a_0 $$

and we have $n$ points $(x_1, y_1)$, $(x_2, y_2)$, $\ldots$, $(x_n, y_n)$.
Then, there is a unique polynomial $f(x)$ of degree $n-1$ such that $f(x_i) = y_i$ for $i = 1, 2, \ldots, n$.

## Shamir's Secret Sharing

Ok now let's connect this idea to Shamir's Secret Sharing.
Suppose you encode a **secret $k$ as a number**.
Let's say a private key for a Bitcoin wallet.
As you've already know, a private key is just a [very big number](/posts/2024-02-05-crypto-basics.html).

You want to split this secret into **$N$ parts**, called **shares**.
You also want to specify a **threshold $T$** such that the **secret $k$ can only be reconstructed if at _least_ $T$ shares are combined**.
Here's how you can use polynomial interpolation to achieve this.

The idea is to use polynomial interpolation to generate a polynomial $f(x)$ of degree $T-1$ such that $f(0) = k$.
In other words, the polynomial $f(x)$ when evaluated at $x = 0$ should give you the secret $k$.
Then, you can **generate $N$ shares by evaluating $f(x)$ at $N$ different points**.

Here's an example with $T = 4$ and $N = 5$.
Our secret is $k = 5$ and since $T = 4$, we generate a polynomial of degree $T-1 = 3$.
We've chosen the polynomial $f(x) = 2x^3 - 3x^2 + 2x + 5$.
Then, we evaluate $f(x)$ at $N = 5$ different points to generate the shares.

![Shamir's Secret Sharing with $N=5$ and $T=4$](/images/shamir.svg)

Now this polynomial is **guaranteed to pass through the point $(0, k)$**.
Hence if you evaluate **$f(0)$ you get the secret $k$**.
To know the secret, you **need to know the polynomial $f(x)$**.
And to know the polynomial $f(x)$, you **need to know at least $T$ shares**.
Otherwise, you **can't reconstruct the polynomial and hence the secret**.

In this setup we generate addresses from the extended public key (xpub) of a Bitcoin wallet that has the private key $k$.
Then, we split the private key into shares and distribute them to different people.
Only if at least $T$ people come together, they can reconstruct the private key and spend the funds.

## Rotating Shares

Note that there's nothing special about the points

- $(-2, f(-2))$
- $(-1, f(-1))$
- $(\frac{1}{2}, f(\frac{1}{2}))$
- $(1, f(1))$
- $(2, f(2))$

that we've used in the previous example.
You could have chosen **any other $N$ points and the polynomial would still be the same**.

Suppose now that your share buddy has lost his share.
Then, the participants can get together and **generate a new polynomial evaluation at any point $n \notin \\{ -2, -1, \frac{1}{2}, 1, 2 \\}$**.

This is exactly what the image below shows:

![Shamir's Secret Sharing with $N=5$ and $T=4$](/images/shamir-alternate_single.svg)

Here we've replaced the point $(-2, f(-2))$ with the point $(3, f(3))$.
We also assume that the point $(-2, f(-2))$ is lost.
The **polynomial is still the same**, and the secret can still be reconstructed if at least $T$ shares are combined.

We can also **rotate all the shares**.
This is shown in the image below:

![Shamir's Secret Sharing with $N=5$ and $T=4$](/images/shamir-alternate_multiple.svg)

Here **all previous points have been replaced by new points**.

## The Polynomial King

> I am the [~~Lizard~~ Polynomial King, I can do anything!](https://youtu.be/ashTaoGrR2o?t=642)
>
> Jim Morrison

In the end **if you somehow know the polynomial $f(x)$, you can do anything**.
You can rug-pull all you share buddies and take all the funds.

There are several ways that a malicious actor could learn the polynomial.
For example, if the shares are generated in a predictable way, an attacker could guess the polynomial.
Or, during the reconstruction phase, an attacker could learn the polynomial by observing the shares.
Additionally, during a distributed share generation, an attacker could disrupt the process
and force the participants to reveal their shares[^nonces].

[^nonces]: Or force them to reuse nonces. Then, "poof", private keys are gone.

## Conclusion

In this post, **we've seen how polynomial interpolation can be used to split a secret into multiple shares**.
We've also seen how the **secret can be reconstructed if a certain number of shares are combined**.
This is the basic idea behind **Shamir's Secret Sharing (SSS)**.

Note that the devil is in the details.
A lot of the complexities of SSS come from the **details of how the shares are generated and how the secret is reconstructed**.
There are **several types of attacks that can be done by a malicious actor**.
Especially during the share generation and reconstruction phases.

The intent of this blog post is to show how **elegant, simple and powerful the idea behind SSS is**.
