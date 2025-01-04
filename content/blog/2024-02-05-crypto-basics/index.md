+++
title = "Basics of Cryptographic Signatures"
date = "2024-02-05T18:53:28"
author = "Jose Storopoli, PhD"

[taxonomies]
tags = ["cryptography", "bitcoin"]

[extra]
katex = true
+++

{% admonition(type="warning", icon="warning", title="Evil JavaScript") %}
This post uses [KaTeX](https://katex.org/) to render mathematical expressions.

To see the rendered mathematical expressions, you'll need to enable JavaScript.
{% end %}

![Euclid's one-way function](euclid.webp)

This is the companion post to the [cryptography workshop](https://github.com/storopoli/cryptography-workshop)
that I gave at a local BitDevs.
Let's explore the basics of cryptography.
We'll go through the following topics:

- One-way functions
- Hash functions
- Public-key cryptography
- DSA
- Schnorr
- Why we don't reuse nonces?
- Why we can combine Schnorr Signatures and not DSA?

## One-way functions

A one-way function is a **function that is easy to compute on every input,
but hard to invert given the image of a random input**.
For example, imagine an omelet.
It's easy to make an omelet from eggs,
but it's hard to make eggs from an omelet.
In a sense we can say that the function $\text{omelet}$ is a one-way function

$$\text{omelet}^{-1}(x) = \ldots$$

That is, we don't know how to invert the function $\text{omelet}$ to get the original eggs back.
Or, even better, **the benefit we get from reverting the omelet to eggs is not worth the effort,
either in time or money**.

Not all functions are one-way functions.
The exponential function, $f(x) = e^x$, is not a one-way function.
It is easy to undo the exponential function by taking the natural logarithm,

$$f^{-1}(x) = \ln(x)$$

To showcase one-way functions, let's take a look at the following example.
Let's play around with some numbers.
Not any kind of numbers, but very special numbers called **primes**.
A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself.

If I give you a big number $n$ and ask you to find its prime factors,
and point a gun at your head,
you'll pretty much screwed.
There's no known efficient algorithm to factorize a big number into its prime factors.
You'll be forced to test all numbers from 2 to $\sqrt{n}$ to see if they divide $n$.

Here's a number:

$$90809$$

What are its prime factors?
It's $1279 \cdot 71$.
Easy to check, right?
Hard to find.
That's because prime factorization, if you choose a fucking big number, is a one-way function.

## Hash Functions

Let's spice things up.
There is a special class of one-way functions called **hash functions**.

**A hash function is any function that can be used to map data of arbitrary size to fixed-size values**.

But we are most interested in **_cryptographic_ hash functions**,
which are hash functions that have statistical properties desirable for cryptographic application:

- **One-way function**: easy to compute $y = f(x)$, hard as fuck to do the opposite, $x = f^{-1}(y)$.
- **Deterministic**: given a function that maps elements from set $X$ to set $Y$, $f: X \to Y$,
  for every $x \in X$ there's _at least one_ $y \in Y$.
  This means that if I give you a certain input, it will always map to the same output.
  It is deterministic.
- **Collision resistance**: the possible values of $f: X \to Y$ follows a uniform distribution,
  that is, given the size of the set $Y$,
  it is hard to find two $x_1, x_2 \in X$ that have the same $y \in Y$ value.
  This property is really important because if an attacker wants to brute-force the
  hash function, there's no option than searching uniformly across the whole possible
  space of possible values that the hash function outputs.

These properties make enable cryptographic hash functions to be used in a wide range of applications,
including but not limited to:

- **Digital signatures**: Hash functions are used to create a digest of the message to be signed.
  The digital signature is then generated using the hash, rather than the message itself,
  to ensure integrity and non-repudiation.

- **Password hashing**: Storing passwords as hash values instead of plain text.
  Even if the hash values are exposed,
  the original passwords remain secure due to the pre-image resistance property.

- **Blockchain and cryptocurrency**: Hash functions are used to maintain the integrity of the blockchain.
  Each block contains the hash of the previous block, creating a secure link.
  Cryptographic hashes also underpin various aspects of cryptocurrency transactions.

- **Data integrity verification**: Hash functions are used to ensure that files, messages,
  or data blocks have not been altered.
  By comparing hash values computed before and after transmission or storage,
  any changes in the data can be detected.

We'll cover just the **digital signatures** part in this post.

### SHA-2 and its variants

The Secure Hash Algorithm 2 (SHA-2) is a set of cryptographic hash functions designed by the National Security Agency (NSA).
It was first published in 2001.

It is composed of six hash functions with digests that are 224, 256, 384, 512, 512/224, and 512/256 bits long:

- `SHA-224`
- `SHA-256`
- `SHA-384`
- `SHA-512`
- `SHA-512/224`
- `SHA-512/256`

Amongst these, let's focus on SHA-256, which is the most widely used while also being notoriously adopted by bitcoin.

SHA-256 does not have any known vulnerabilities and is considered secure.
It comprises of 32-bit words and operates on 64-byte blocks.
The algorithm does 64 rounds of the following operations:

- `AND`: bitwise boolean AND
- `XOR`: bitwise boolean XOR
- `OR`: bitwise boolean OR
- `ROT`: right rotation bit shift
- `ADD`: addition modulo $2^{32}$

You can check [SHA-256 Pseudocode on Wikipedia](https://en.wikipedia.org/wiki/SHA-2#Pseudocode).
It really scrambles the input message in a way that is very hard to reverse.

These operations are non-linear and very difficult to keep track of.
In other words, you can't reverse-engineer the hash to find the original message.
There's no ["autodiff"](https://en.wikipedia.org/wiki/Automatic_differentiation) for hash functions.

Since it is a cryptographic hash function,
if we change just one bit of the input,
the output will be completely different.
Check this example:

```bash
$ echo "The quick brown fox jumps over the lazy dog" | shasum -a 256
c03905fcdab297513a620ec81ed46ca44ddb62d41cbbd83eb4a5a3592be26a69  -

$ echo "The quick brown fox jumps over the lazy dog." | shasum -a 256
b47cc0f104b62d4c7c30bcd68fd8e67613e287dc4ad8c310ef10cbadea9c4380  -
```

Here we are only adding a period at the end of the sentence,
and the hash is completely different.
This is due to the property of collision resistance that we mentioned earlier.

## Fields

Before we dive into public-key cryptography,
we need a brief interlude on fields.

**[Fields](<https://en.wikipedia.org/wiki/Field_(mathematics)>) are sets with two binary operations,
called addition $+$ and multiplication $\times$**.
We write

$$F = (F, +, \times)$$

to denote a field,
where $F$ is the set, $+$ is the addition operation,
and $\times$ is the multiplication operation.

Addition and multiplication behave similar to the addition and multiplication of real numbers.
For example, addition is **commutative** and **associative**

$$a + b = b + a,$$

and multiplication is **distributive**

$$a \times (b + c) = a \times b + a \times c.$$

Also, there are two special elements in the field,
called the **additive identity** $-a$ and the **multiplicative identity** $a^{-1}$,
such that

$$a + (-a) = I,$$

and

$$a \times a^{-1} = I,$$

where $I$ is the identity element.

Note that this allows us to define **subtraction**

$$a - b = a + (-b),$$

and **division**

$$a \div b = a \times b^{-1}.$$

### Finite Fields

Now we are ready for finite fields.
A [_finite field_](https://en.wikipedia.org/wiki/Finite_field), also called a Galois field (in honor of Évariste Galois),
is a **field with a finite number of elements.
As with any field, a finite field is a set on which the operations of multiplication,
addition, subtraction and division are defined and satisfy the rules above for fields**.

Finite fields is a very rich topic in mathematics,
and there are many ways to construct them.
The easiest way to construct a finite field is to take the **integers modulo a prime number $p$**.
For example $\mathbb{Z}_5$ is a finite field with 5 elements:

$$\mathbb{Z}_5 = \lbrace 0, 1, 2, 3, 4 \rbrace.$$

In general, $\mathbb{Z}_n$ is a finite field with $n$ elements:

$$\mathbb{Z}_n = \lbrace 0, 1, 2, \ldots, n - 1 \rbrace.$$

**The number of elements in a finite field is called the _order_ of the field**.
The order of a finite field is **always a prime number $p$**.
The $\mathbb{Z}_5$ example above is a finite field of order 5.
However, $\mathbb{Z}_4$ is not a finite field,
because 4 is not a prime number, but rather a composite number.

$$4 = 2 \times 2.$$

And we can write $\mathbb{Z}_4$ as

$$\mathbb{Z}_4 = 2 \times \mathbb{Z}_2.$$

This means that every element in $a \in \mathbb{Z}_4$ can be written as

$$a = 2 \times b,$$

where $b$ is an element in $\mathbb{Z}_2$.

Hence, not every element of $\mathbb{Z}_4$ is unique, and they are equivalent to the elements in $\mathbb{Z}_2$.

In general if $n$ is a composite number,
then $\mathbb{Z}_n$ is not a finite field.
However, if $n = r \times s$ where $r$ and $s$ are prime numbers,
and $r < s$,
then $\mathbb{Z}_n$ is a finite field of order $r$.

#### Operations in Finite Fields

**Addition** in finite fields is defined as the remainder of the sum of two elements modulo the order of the
field.

For example, in $\mathbb{Z}_3$,

$$1 + 2 = 3 \mod 3 = 0.$$

We can also define subtraction in finite fields as the remainder of the difference of two elements modulo the order of the field.

For example, in $\mathbb{Z}_3$,

$$1 - 2 = -1 \mod 3 = 2.$$

Multiplication in finite fields can be written as multiple additions.
For example, in $\mathbb{Z}_3$,

$$2 \times 2 = 2 + 2 = 4 \mod 3 = 1.$$

Exponentiation in finite fields can be written as multiple multiplications.
For example, in $\mathbb{Z}_3$,

$$2^2 = 2 \times 2 = 4 \mod 3 = 1.$$

As you can see addition, subtraction, and multiplication becomes linear operations.
This is very trivial for any finite field.

However, for division we are pretty much screwed.
It is really hard to find the multiplicative inverse of an element in a finite field.
For example, suppose that we have numbers $a,b$ in a very large finite field $\mathbb{Z}_p$,
such that

$$c = a \times b \mod p.$$

Then we can write division as

$$a = c \div b = c \times b^{-1} \mod p.$$

Now we need to find $b^{-1}$, which is the multiplicative inverse of $b$.
This is called the [**_discrete logarithm problem_**](https://en.wikipedia.org/wiki/Discrete_logarithm).
Because we need to find $b^{-1}$ such that

$$b^{-1} = \log_b c \mod p.$$

Since this number is a discrete number and not a real number,
that's why it's called the discrete logarithm problem.

Good luck my friend, no efficient method is known for computing them in general.
You can try brute force, but that's not efficient.

#### Why the Discrete Logarithm Problem is Hard as Fuck

To get a feeling why the discrete logarithm problem is difficult,
let's add one more concept to our bag of knowledge.
Every finite field has _**generators**_,
also known as _**primitive roots**_,
which is also a member of the group,
such that applying multiplication to this one single element
makes possible to generate the whole finite field.

Let's illustrate this with an example.
Below we have a table of all the results of the following operation

$$b^x \mod 7$$

for every possible value of $x$.
As you've guessed right this is the $\mathbb{Z}_7$ finite field.

| $b$ | $b^1 \mod 7$ | $b^2 \mod 7$ | $b^3 \mod 7$ | $b^4 \mod 7$ | $b^5 \mod 7$ | $b^6 \mod 7$ |
| :-: | :----------: | :----------: | :----------: | :----------: | :----------: | :----------: |
| $1$ |     $1$      |     $1$      |     $1$      |     $1$      |     $1$      |     $1$      |
| $2$ |     $2$      |     $4$      |     $1$      |     $2$      |     $4$      |     $1$      |
| $3$ |     $3$      |     $2$      |     $6$      |     $4$      |     $5$      |     $1$      |
| $4$ |     $4$      |     $2$      |     $1$      |     $4$      |     $2$      |     $1$      |
| $5$ |     $5$      |     $4$      |     $6$      |     $2$      |     $3$      |     $1$      |
| $6$ |     $6$      |     $1$      |     $6$      |     $1$      |     $1$      |     $1$      |

You see that something interesting is happening here.
For specific values of $b$, such as $b = 3$, and $b = 5$, we are able to **generate the whole finite field**.
Hence, say that $3$ and $5$ are _**generators**_ or _**primitive roots**_ of $\mathbb{Z}_7$.

Now suppose I ask you to find $x$ in the following equation

$$3^x \mod p = 11$$

where $p$ is a very large prime number.
Then you don't have any other option than brute forcing it.
**You'll need to try each exponent $x \in \mathbb{Z}_p$ until you find the one that satisfies the equation**.

Notice that this operation is very asymmetric.
It is very easy to compute $3^x \mod p$ for any $x$,
but it is very hard to find $x$ given $3^x \mod p$.

Now we are ready to dive into public-key cryptography.

#### Numerical Example of the Discrete Logarithm Problem

Let's illustrate the discrete logarithm problem with a numerical example.

1. **Choose a prime number $p$**. Let's pick $p = 17$.
1. **Choose a generator $g$ of the group**.
   For $p = 17$, we can choose $g = 3$ because $3$ is a primitive root of $\mathbb{Z}_{17}$.
1. **Choose an element $x$**.
   Let's pick $x = 15$.

The discrete logarithm problem is to find $x$ given $g^x \mod p$.
So let's plug in the numbers; find $x$ in

$$3^x = 15 \mod 17 $$

Try to find it.
Good luck.

> [](<$block.attrs('info')>)
> The answer is $x = 6$. This means that $3^6 = 15 \mod 17$.

## Public-key cryptography

Public-key cryptography, or asymmetric cryptography, is a cryptographic system that uses pairs of keys:
private and public.
The public key you can share with anyone,
but the private key you must keep secret.
The keys are related mathematically,
but it is computationally infeasible to derive the private key from the public key.
In other words, the public key is a one-way function of the private key.

Before we dive into the details of the public-key cryptography, and signing and verifying messages,
let me introduce some notation:

- $p$: big fucking huge prime number (4096 bits or more)
- $\mathbb{Z}_p$: the finite field of order $p$
- $g$: a generator of $\mathbb{Z}_p$
- $S_k$: secret key, a random integer in the finite field $\mathbb{Z}_p$
- $P_k$: public key derived by $P_k = g^{S_k}$

If you know $S_k$ and $g$ (which is almost always part of the spec),
then it's easy to derive the $P_k$.
However, if you only know $g$ and $P_k$, good luck finding $S_k$.
It's the discrete log problem again.
And as long $p$ is HUGE you are pretty confident that no one will find your secret key
from your public key.

Now what we can do with these keys and big prime numbers?
We'll we can sign a message with our secret key and everyone can verify the authenticity of
the message using our public key.
The message in our case it is commonly a hash function of the "original message".
Due to the collision resistance property, we can definitely assert that:

1. the message has not been altered
1. the message was signed by the owner of the private key

Fun fact, I once gave a recommendation letter to a very bright student,
that was only a plain text file signed with my private key.
I could rest assured that the letter was not altered,
and the student and other people could verify that I was the author of the letter.

Next, we'll dive into the details of the Digital Signature Algorithm (DSA)
and the Schnorr signature algorithm.

## DSA

DSA stands for [Digital Signature Algorithm](https://en.wikipedia.org/wiki/Digital_Signature_Algorithm).
It was first proposed by the National Institute of Standards and Technology (NIST) in 1991.
Note that [OpenSSH announced that DSA is scheduled for removal in 2025](https://lwn.net/Articles/958048/).

Here's how you can sign a message using DSA:

1. Choose two prime numbers $p, q$ such that $p - 1 \mod q = 0$ (e.g., 1279 and 71).
1. Choose your private key $S_k$ as a random integer $\in [1, q-1]$.
1. Choose a generator $g$.
1. Compute your public key $P_k$: $g^{S_k} \mod p$.
1. Choose your nonce $k$: as a random integer $\in [1, q-1]$.
1. Compute your "public nonce" $K$: $(g^k \mod p) \mod q$ (also known as $r$).
1. Get your message ($m$) through a cryptographic hash function $H$: $H(m)$.
1. Compute your signature $s$: $(k^{-1} (H(m) + S_k K)) \mod q$.
1. Send to your buddy $(p, q, g)$, $P_k$, and $(K, s)$.

And here's how you can verify the signature:

1. Compute $w = s^{-1} \mod q$.
1. Compute $u_1 = H{m} \cdot w \mod q$.
1. Compute $u_2 = K \cdot w \mod q$.
1. Compute $K^\* = {g^{u_1} P^{u_2}_k \mod p} \mod q$.
1. Assert $K = K^\*$.

How this works?
Let's go through a proof of correctness.
I added some comments to every operation in parentheses to make it easier to follow.

1. $s = k^{-1} \cdot {H + S_k K} \mod q$ ($\mod p$ and $H(m)$ implicit).
1. $k = s^{-1} \cdot {H + S_k K} \mod q$ (move $s$ to $k$).
1. $k = H \cdot s^{-1} + S_k K \cdot s^{-1} \mod q$ (distribute $s^{-1}$).
1. $k = H \cdot w + S_k K \cdot w \mod q$ ($w = s^{-1}$).
1. $g^k = g^{H \cdot w + S_k K \cdot w \mod q}$ (put $g$ in both sides).
1. $g^k = g^{H \cdot w \mod q} \cdot g^{S_k K \cdot w \mod q}$ (product of the exponents).
1. $g^k = g^{H \cdot w \mod q} \cdot P^{K \cdot w \mod q}_k$ ($P_k = g^{S_k}$).
1. $g^k = g^{u_1} \cdot P^{u_2}_k$ (replace $u_1$ and $u_2$).
1. $K = K^\*$ (replace $K$ and $K^*$).

There you go.
This attest that the signature is correct and the message was signed by the owner of the private key.

## Schnorr

[Schnorr signature algorithm](https://en.wikipedia.org/wiki/Schnorr_signature)
is a very similar algorithm to DSA.
It was proposed by Claus-Peter Schnorr in 1989.
It is considered to be more secure than DSA and is also more efficient.
The patent for Schnorr signatures expired in 2008,
just in time for Satoshi to include it in Bitcoin.
However, it was probably not included due to the fact that there wasn't
good battle-tested software implementations of it at the time.
However, it was added to Bitcoin in the Taproot upgrade.

Schnorr is a marvelous algorithm.
It is so much simpler than DSA.
Here's how you sign a message using Schnorr:

1. Choose a prime number $p$.
1. Choose your private key $S_k$ as a random integer $\in [1, p-1]$.
1. Choose a generator $g$.
1. Compute your public key $P_k$: $g^{S_k}$.
1. Choose your nonce $k$: as a random integer $\in [1, p-1]$.
1. Compute your "public nonce" $K$: $g^k \mod p$ (also known as $r$).
1. Get your message ($m$) through a cryptographic hash function $H$ concatenating with $K$: $e = H(K || m)$.
1. Compute your signature $s$: $k - S_k e$.
1. Send to your buddy $(p, g)$, $P_k$, and $(K, s)$.

And here's how you can verify the signature:

1. Compute $e = H(K || m)$.
1. Compute $K^\* = g^s P_k^e$.
1. Compute $e^\* = H(K^* || m)$.
1. Assert $e = e^\*$.

How this works?
Let's go through a proof of correctness.
As before, I added some comments to every operation in parentheses to make it easier to follow.

1. $K^\* = g^s P_k^e$ ($\mod p$ implicit).
1. $K^\* = g^{k - S_k e} g^{S_k e}$ ($s = k - S_k e$ and $P_k = g^{S_k}$).
1. $K^\* = g^k$ (cancel $S_k e$ in the exponent of $g$).
1. $K^\* = K$ ($K = g^k$).
1. Hence $H(K^* || m) = H(K || m)$.

There you go.
This attest that the signature is correct and the message was signed by the owner of the private key.

## Why we don't reuse nonces?

Never, ever, reuse a nonce.
Why?
First, because nonce is short for "number used once".
It is supposed to be used only once.
Because if you reuse a nonce, then you are pretty much screwed.
An attacker can derive your private key from two signatures with the same nonce.
This is called the "nonce reuse attack".

Fun fact: this is what happened to the
[PlayStation 3](https://en.wikipedia.org/wiki/PlayStation_3_homebrew#Private_key_compromised).

Let's see how we can derive the private key from two signatures with the same nonce.
Here we are in a context that we have two signatures $s$ and $s^\prime$,
both using the same nonce $k = k^\prime$.

First, let's do the ~~ugly~~ DSA math:

$$
\begin{aligned}
  s^\prime - s &= (k^{\prime {-1}} (H(m_1) + S_k K')) - (k^{-1} (H(m_2) + S_k K)) \\\\
  s^\prime - s &= k^{-1} (H(m_1) - H(m_2)) \\\\
  k &= (H(m_1) - H(m_2)) (s^\prime - s)^{-1}
\end{aligned}
$$

Now remember you know $s$, $s^\prime$, $H(m_1)$, $H(m_2)$ $K$, and $K^\prime$.
Let's do the final step and solve for $S_k$:

$$S_k = K^{-1}  (k s - H(m_1))$$

Now let's do the Schnorr math.
But in Schnorr, everything is simpler.
Even nonce reuse attacks.

$$s\^\prime - s = (k\^\prime - k) - S_k (e\^\prime - e)$$

If $k\^\prime = k$ (nonce reuse) then you can easily isolate $S_k$ with simple algebra.

Remember: you know $s\^\prime, s, e, e\^\prime$ and $k\^\prime - k = 0$.

## Why we can combine Schnorr Signatures and not DSA?

In Bitcoin, we can combine Schnorr signatures and not DSA.
Why?
Because Schnorr signatures are linear.
This means that you can add two Schnorr signatures and get a valid signature for the sum of the messages.
This is not possible with DSA.
This is called the "linearity property" of Schnorr signatures.

Remember that in $Z_p$ addition, multiplication, and exponentiation,
i.e anything with $+, \cdot, -$, are linear operations
However, division (modular inverse),
.i.e anything that is $^{-1}$, is not linear.
That is:

$$x^{-1} + y^{-1} \ne (x + y)^{-1}.$$

Here's a trivial python code that shows that modular inverse is not linear:

```python
>>> p = 71; x = 13; y = 17;
>>> pow(x, -1, p) + pow(y, -1, p) == pow(x + y, -1, p)
False
```

Let's revisit the signature step of DSA and Schnorr:

- DSA: $s = k^{-1} (H(m) + S_k K)$
- Schnorr: $s = k - S_k H(K || m)$

So if you have two Schnorr signatures $s_1$ and $s_2$ for two messages $m_1$ and $m_2$,
then you can easily compute a valid signature for the sum of the messages $m_1 + m_2$:

$$s = s_1 + s_2$$

Also note that we can combine Schnorr public keys:

$$P^\prime_k + P_k = g^{S^\prime_k} + g^{S_k} = g^{S_k^\prime + S_k}$$

And the signature $s$ for the sum of the messages $m_1 + m_2$
can be verified with the public key $P^\prime_k + P_k$.

This is not possible with DSA.

Because the signature step in DSA is not linear,
it has a $k^{-1}$ in it.

## Technical Interlude: Elliptic Curves

Technically speaking, Bitcoin uses the Elliptic Curve Digital Signature Algorithm (ECDSA),
and the Schnorr signature algorithm is based on the same elliptic curve (EC) as ECDSA.

And trivially speaking EC public-key cryptography in the end is just a finite field
on $\mathbb{Z}_p$.
It has everything that we've seen so far:

- Addition
- Subtraction
- Multiplication
- Division
- Exponentiation
- Generators
- Discrete Logarithm Problem

## Conclusion

I hope you enjoyed this companion post to the
[cryptography workshop](https://github.com/storopoli/cryptography-workshop).
Remember don't reuse nonces.
