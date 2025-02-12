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

This post has a lot of overlaps with my previous post on
["Some Intuitions on Zero-Knowledge Proofs"](@/blog/2024-06-08-zkp/index.md).
If you want to know more about Zero-Knowledge Proofs (ZKPs),
then I'd suggest you read that post first.

{% admonition(type="tip", icon="tip", title="Links and Footnotes") %}
This post is filled with external links and footnotes.
If you want to dive deeper into any topic that has one of these,
feel free to do so.
The idea was to give a general overview the concepts,
while also allowing you to tune your experience by giving you
a bunch of tangents and rabbit holes to explore if wanted.
{% end %}

**BitVM is a bridge between Bitcoin and a sidesystem**.
Generally, these bridges are secured by a federated multisig,
where to bridge-out you need to have a majority of the federation.
Mathematically, this is a $(\frac{N}{2}+1)$-of-$N$ trust model.
This is not ideal since it's a "trust me bro" situation and the "bros"
are the majority of the bridge.
BitVM is different, since it can drastically reduce the trust assumptions.
It is a **$1$-of-$N$ trust model, in which as long as you have a live honest operator,
you can withdraw on-chain**.

I'm going to present BitVM in it's main three big ideas:

1. **Verified Computation**
2. **Groth16 Bitcoin Script Compiler**
3. **Emulating Covenants with Connector Outputs**

![Three Big Ideas](3_big_ideas.png)

The only new idea that BitVM brings to the table is the Groth16 Bitcoin script compiler.
Arithmetic circuits are basic building blocks of ZK-SNARKs,
and emulating covenants with connector outputs was already used by the
[Ark protocol](https://ark-protocol.org/).

## Big Idea 1: Verified Computation

Suppose you have a function that does some complicated stuff and performs some computation.
Then, this function can be represented as an [**arithmetic circuit**](https://en.wikipedia.org/wiki/Arithmetic_circuit)[^peano].

[^peano]:
    If you want to dig yourself into a very nice rabbit hole,
    check [Peano arithmetic](https://en.wikipedia.org/wiki/Peano_axioms)
    and [Turing-completeness relations](https://en.wikipedia.org/wiki/Turing_completeness).

An arithmetic circuit is a directed acyclic graph (DAG) where:

- Every indegree-zero node is an input gate that represents a variable $x_i$
- Every node with indegree $>1$ is either:
  - an addition gate, $+$, that represents the sum of its children
  - a multiplication gate, $\times$, that represents the product of its children

Here's an example of an arithmetic circuit that represents the function

$$f(x_1, x_2) = x_1 \cdot x_2 + x_1$$

{% mermaid() %}
flowchart TD
x1["x₁"]
x2["x₂"]
mul["×"]
add["\+"]

x1 --> mul
x2 --> mul
mul --> add
x1 --> add
{% end %}

In the circuit above, the input gates are
$x_1$ and $x_{2}$,
the product gate computes $x_1 \cdot x_2$,
and the sum gate computes the result of the product gate added to $x_1$.
All of this evaluates to $x_1 \cdot x_2 + x_1$.

This stems due to the fact that any [NP problem](<https://en.wikipedia.org/wiki/NP_(complexity)>)[^np-complete]
can be reduced in polynomial time by a deterministic Turing machine to
the [Boolean satisfiability problem](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem)[^boolean-funs].
This is known as the [Cook-Levin theorem](https://en.wikipedia.org/wiki/Cook–Levin_theorem),
and it is a fundamental result in theoretical computer science.

[^np-complete]: Actually, it is any NP-complete problem, but without loss of generality, we'll focus on NP.

[^boolean-funs]: Note that you can represent addition and multiplication as Boolean functions.

In computer science, we have two main classes of problems:

- $\cal{P}$ problems, which are **easy to solve and verify**.
- $\cal{NP}$ problems, which are **hard to solve, but _easy_ to verify**.

$\cal{P}$ stems from polynomial time,
and contains all decision problems that can be solved by a deterministic Turing machine
using a polynomial amount of computation time, or polynomial time.
$\cal{NP}$ stems from non-deterministic polynomial time,
and is the set of decision problems for which the problem instances,
where the answer is "yes", have proofs verifiable in polynomial time by
a deterministic Turing machine.

![P vs NP](p_np.png)

According to the Cook-Levin theorem,
once you find an algorithm that solves one of the $\cal{NP}$ problems
in polynomial time, you can use it to solve **_any_ $\cal{NP}$ problem
in polynomial time**.
But we haven't yet found such algorithms for any $\cal{NP}$ problem.
Heck, we don't even know if $\cal{P} \ne \cal{NP}$.
It is highly speculated, but yet still an open question[^millennium-problems].

[^millennium-problems]:
    If you solve this conjecture either by proving it or disproving it,
    you'll be up for a [1 million USD prize](https://en.wikipedia.org/wiki/Millennium_Prize_Problems).
    I like to say that it is the hardest way to
    earn 1 million USD.

Moving on, **any (finite) arithmetic circuit can be transformed
into a big (finite) polynomial**,
by using techniques such as
[Rank-1 Constraint System (R1CS), quadratic arithmetic program (QAP)](https://alinush.github.io/qap-r1cs);
and many others.
This means that we can map any arithmetic circuit to a polynomial,
and vice-versa; and one operation in each side of the map,
can be mapped to a single operation in the other side.

Finally, we can **cryptographically commit to a polynomial using
[polynomial commitment schemes (PCS)](https://en.wikipedia.org/wiki/Commitment_scheme#KZG_commitment)**.
This means that we **also commit to a certain arithmetic circuit,
given that we know the unique polynomial that it represents**.
This commitment allow us to create **very succinct zero-knowledge proofs
that some computation was performed given certain inputs**.
We can represent this with proof as $\pi$
which takes as public-accessible inputs $x$,
and private-accessible inputs $w$ (as in witness),
and outputs $y$:

$$\pi(x; w) = y$$

Let's define verifier $V$ that has access to the arithmetic circuit $C$,
the inputs $x$, and the proof $\pi$.
Note that $V$ does not have access to the witness $w$, which are private inputs.
Additionally, $V$ may or may not have access to the output $y$ of the whole computation.
Also, we'll define a prover $P$ that has access to everything $V$ has,
with the addition of the witness $w$.

This proof $\pi$ has three main properties:

1. **Completeness**: If the statement is true, the verifier will accept the proof.

   $$ \Pr\big[V(\pi, x) = \text{accept} \big] = 1. $$

   Here $\Pr\big[V(\pi(x)) = \text{accept} \big]$
   denotes the probability that the verifier accepts the proof given
   a proof $\pi$, and inputs $x$.

1. **Soundness**: If the statement is true, no cheating prover
   can convince an honest verifier that it is true,
   except with some negligible probability [^negligible].

   $$ \forall A, \forall x, \forall \pi: \Pr\big[V(A, \pi, x) = \text{accept} \big] < \text{negligible}. $$

   Here $\Pr\big[V(A, \pi) = \text{accept} \big]$ denotes
   the probability that the verifier accepts the proof given an adversary $A$,
   a proof $\pi$, and inputs $x$.

1. **Zero-Knowledge**: If the statement is true,
   the verifier learns nothing about the secret $x$.

[^negligible]:
    A function $f$ is negligible if for every polynomial $p$,
    there exists an $N$ such that for all $n > N$,
    $$ f(n) < \frac{1}{p(n)}. $$
    If you want to learn more about negligible functions,
    read Chapter 3, Section 3.1 of the book [Introduction to Modern Cryptography](https://doi.org/10.1201/9781420010756) by Katz & Lindell.

There are many commitment schemes,
even ones that don't use polynomials.
But a succinct zero knowledge system also needs an
interactive oracle proof (IOP).
One of such schemes is [Groth16](https://alinush.github.io/groth16),
named after Jens Groth,
who published the paper describing it in 2016.

**Groth16 uses a mathematical tool called
[bilinear maps](https://en.wikipedia.org/wiki/Bilinear_map)
or [pairing functions](https://alinush.github.io/2022/12/31/pairings-or-bilinear-maps.html)**.
This is generally applied to vector spaces,
but they can work in elliptic curves (EC) as well.
It allows us to have VERY succinct proofs.
I'm not gonna cover the math behind EC pairings.
Instead, suffices to know that an EC pairing,
given three groups $G_1$, $G_2$, and $G_T$ (as in target group),
is a function $e$:

$$e: G_1 \times G_2 \rightarrow G_T$$

In other words, it takes any two elements in $G_1$ and $G_2$;
and outputs a group element in $G_T$.

**Groth16 proofs are very succinct**.
It consists of 3 group elements
(2 from $G_1$ and 1 from $G_2$) which amounts **from 128 to 192 bytes**.

As an example suppose that I know how to calculate the 100th million digit of $\pi$.
I publicly produce a VERY big arithmetic circuit,
and cryptographically commit to it using a polynomial commitment scheme.
I proceed by performing the HUGE computation, and sending to you, the prover,
$x$ and $\pi$: the inputs to this circuit and the proof
that I've performed the computation correctly.
By verifying the proof, you can convince yourself that I know the
100th million digit of $\pi$ without gaining any knowledge of this digit at all.

In fact, to classify as **succinct**, this proving system must
output proofs that are **at most poly-logarithmic** in the size of the circuit $C$,
denoted as $|C|$,
that it was committed and used to perform the computation
that the prover wants to prove.
Additionally, the verification time must also be poly-logarithmic in $C$.
This means that **both the proof size
and verification time complexity must be at most**:

$$O(\log^k |C|)$$

for some constant $k>1$.

Since Groth16, outputs proofs that are between 128 and 192 bytes,
and also has a **constant-time verification**,
due to the face that it is just checking 3 group elements,
irrespectively of the size of the circuit $C$,
then **Groth16 is a succinct zero-knowledge proof system**.
In fact, it is currently the most succinct one that we know so far[^research].

[^research]:
    Note that ZK-SNARKs and succinct proving systems in general are a very hot research topic.
    We might find succincter systems in the future.

This is something quite marvelous.
Imagine that you have ANY computation whatsoever,
and I can prove to you that I've done it
by sending only a very succinct ~200-byte proof
and you are completely convinced that I did it.
This is called **[verifiable computing](https://en.wikipedia.org/wiki/Verifiable_computing)**,
which crypto-bros call "zero-knowledge".
We already have zero-knowledge in classical cryptography:
"Hey I know a secret key and here's a signature to prove to you".
But the real novelty here is that **we can prove that I did a computation
without revealing the computation itself**.

To finalize, there are some caveats in using Groth16.
Yes, we have the **best ZK-SNARK in terms of proof size
and verification time**.
However, the setup is what we call a **"trusted setup" that is also non-universal**.
This means that we need some sort of ceremony to setup the protocol,
which includes the prover and verifier keys.
This can be done in a Multi-Party Computation (MPC) style,
with several parties joining the ceremony.
Each one of these parties will contribute with some random secret data
towards the setup of the protocol.
**As long as one of them throw away their secret data,
the protocol is secure**[^ceremony].
This means that no one can prove false statements
or make a proof for a computation that was not performed.
Additionally, the setup is done for a single circuit.
Hence, you can only prove stuff that was done in a simple computation context.
You can vary the inputs as much as you like, but the circuit will always be the same.
To get a different circuit using Groth16, you need to perform a new setup.

[^ceremony]:
    In the infamous Zcash setup ceremony, Peter Todd,
    one of the participants, "ran all of his computations on a laptop encased
    in a tin foil-lined cardboard box, while driving across Canada.
    He then burned his compute node to a crisp with a propane torch".
    [Source](https://spectrum.ieee.org/the-crazy-security-behind-the-birth-of-zcash)

## Big Idea 2: Groth16 Bitcoin Script Compiler

- Groth16 ZK-SNARK compiler for Bitcoin Script:
  - Script in opcodes ~1GB
  - Break into sequentially-ordered standard transactions (<400kb, 1,000 stack elements, 400,000 opcodes, etc.)
  - Pass state from one transaction to the next transaction using bitcommitments (One-time Signatures, OTS, Lamport, Winternitz)
  - P2TR with big merkle trees in the taproot script spending path (NUMS in the key path)

## Big Idea 3: Emulating Covenants with Connector Outputs

- Emulating covenants with connector outputs and pre-signed transactions (and timelocks):
  - Simple case where both Alice and Bob deposit into a P2TR D BTC.
  - This P2TR has a Groth16 verifier that attest that someone has done a (big) computation in an AC.
  - Alice spends from this P2TR by submitting a witness (the Groth16 proof).
  - Groth16 verifier will output connector 1 (C1), or connector (C2) depending on the output of the proof verification.
  - C1 Alice gets the D BTC (Alice has done the computation correctly and the proof is valid)
  - C2 Bob gets the D BTC (Alice has NOT done the computation correctly and the proof is invalid)
- Go over the transaction graph (simplified, not using superblocks, but stake chain).

## Conclusion

The focus of this post is to give a high-level overview of BitVM,
and building intuitions on how it works.

Of course, you need a LOT of engineering to implement BitVM.
If you are curious about the details, you can check out the
[BitVM repo](https://github.com/BitVM/BitVM) for the Groth16 compiler,
the [`strata-bridge`](https://github.com/alpenlabs/strata-bridge) repo
for the whole BitVM bridge transaction graph;
and finally, the [`strata`](https://github.com/alpenlabs/strata) repo
for the Strata rollup (the BitVM sidesystem).
