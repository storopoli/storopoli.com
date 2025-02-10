+++
title = "BitVM: How to bridge using 1-of-N trust assumptions"
date = "2025-02-10T04:57:00"
author = "Jose Storopoli, PhD"

[taxonomies]
tags = ["math", "cryptography", "bitcoin"]

[extra]
katex = true
mermaid = true
+++

{% admonition(type="warning", icon="warning", title="Evil JavaScript") %}
This post uses [KaTeX](https://katex.org/) to render mathematical expressions
and [Mermaid](https://mermaid.js.org) to render flowcharts.

To see the rendered content, you'll need to enable JavaScript.
{% end %}

{% admonition(type="info", icon="info", title="BTC++ Talk") %}
This post is the written version of my very condensed 45-minute talk
at [BTC++ 2025 Floripa](https://btcpp.dev/conf/floripa).
{% end %}

![BitVM Meme](bitvm.jpg)

This post has a lot of overlap with my previous post on
["Some Intuitions on Zero-Knowledge Proofs"](@/blog/2024-06-08-zkp/index.md).
If you want to know more about Zero-Knowledge Proofs (ZKPs),
then I'd suggest you read that post first.

## Give me a computation and I'll give you an arithmetic circuit

Suppose you have a function that does some complicated stuff and performs some computation.
Then, this function can be represented as an [**arithmetic circuit**](https://en.wikipedia.org/wiki/Arithmetic_circuit).

An arithmetic circuit is a directed acyclic graph (DAG) where:

- Every indegree-zero node is an input gate that represents a variable $x_i$
- Every node with indegree $>1$ is either:
  - an addition gate, $+$, that represents the sum of its children
  - a multiplication gate, $\times$, that represents the product of its children

Here's an example of an arithmetic circuit that represents the function
$p(x_1, x_2) = x_2^3 + x_1 x_2^2 + x_2^2 + x_1 x_2$:

{% mermaid() %}
flowchart TD
x1["x₁"]
x2["x₂"]
one["1"]
add1["\+"]
add2["\+"]
mult["×"]
x1 --> add1
x2 --> add2
one --> add2
add2 --> add1
add1 --> mult
add2 --> mult
{% end %}

In the circuit above, the input gates compute (from left to right)
$x_{1},x_{2}$ and $1$,
the sum gates compute $x_{1}+x_{2}$
and $x_{2}+1$,
and the product gate computes $(x_{1}+x_{2})x_{2}(x_{2}+1)$
which evaluates to $x_{2}^{3}+x_{1}x_{2}^{2}+x_{2}^{2}+x_{1}x_{2}$.

This stems due to the fact that any [NP-complete problem](<https://en.wikipedia.org/wiki/NP_(complexity)>)
can be reduced in polynomial time by a deterministic Turing machine to
the [Boolean satisfiability problem](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem).
This is known as the [Cook-Levin theorem](https://en.wikipedia.org/wiki/Cook–Levin_theorem),
and it is a fundamental result in theoretical computer science.
(Note that you can represent addition and multiplication as Boolean functions).

If you want to dig yourself into a very nice rabbit hole,
check [Peano arithmetic](https://en.wikipedia.org/wiki/Peano_axioms)
and [Turing-completeness relations](https://en.wikipedia.org/wiki/Turing_completeness).

Second, any (finite) arithmetic circuit can be transformed into a big (finite) polynomial,
by using techniques such as
[Rank-1 Constraint System (R1CS), quadratic arithmetic program (QAP)](https://alinush.github.io/qap-r1cs);
and many others.

Finally, Using [polynomial commitment schemes (PCS)](https://en.wikipedia.org/wiki/Commitment_scheme#KZG_commitment)
we can create a succinct ZKP that I performed a computation.
[Groth16](https://alinush.github.io/groth16) proof consists of 3 group elements
(2 from $G_1$ and 1 from $G_2$) which amounts to around 200 bytes.

This is something quite marvelous.
Imagine that you have ANY computation whatsoever,
and I can prove to you that I've done it
by sending only a very succinct 200-byte proof
and you are completely convinced that I did it.
This is called [verifiable computing](https://en.wikipedia.org/wiki/Verifiable_computing),
which crypto-bros call "zero-knowledge".
We already have zero-knowledge in classical cryptography:
"Hey I know a secret key and here's a signature to prove to you".
But the real novelty here is that we can prove that I did a computation
without revealing the computation itself.
