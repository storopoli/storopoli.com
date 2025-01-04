+++
title = "Some Intuitions on Zero-Knowledge Proofs"
date = "2024-06-08T15:48:33"
author = "Jose Storopoli, PhD"

[taxonomies]
tags = ["cryptography", "bitcoin"]

[extra]
katex = true
mermaid = true
+++

{% admonition(type="warning", icon="warning", title="Evil JavaScript") %}
This post uses [KaTeX](https://katex.org/) to render mathematical expressions
and [Mermaid](https://mermaid.js.org) to render flowcharts.

To see the rendered content, you'll need to enable JavaScript.
{% end %}

![Zero-knowledge proofs and the meaning of life](zkp_meme.jpg)

Lately, I've been diving a little into the world of **Zero-Knowledge Proofs**.
The idea is to prove that you know something without revealing what you know.
More specifically, a **Zero-Knowledge Proof** is a cryptographic protocol that allows
a **prover** to convince a **verifier** that a statement is true without revealing
any information beyond the validity of the statement.
In essence, by the end of the protocol, the verifier is convinced that the prover knows the secret,
and the **verifier hasn't learned anything (zero-knowledge) about the secret**.

**Zero-Knowledge Proofs** (ZKPs) are kinda hot right now,
since a lot of new Bitcoin innovations are being built on top of them.
It allows for a higher level of privacy and potential scalability improvements
in the Bitcoin network.

Zero-knowledge proofs are advantageous in a myriad of application,
including (refer to `Petkus19`):

- **Proving statement on private data**:

  - Person $A$ has more than $X$ in his bank account
  - In the last year, a bank did not transact with an entity $Y$
  - Matching DNA without revealing full DNA
  - One has a credit score higher than $Z$

- **Anonymous authorization**:

  - Proving that requester $R$ has right to access web-site's restricted area without revealing its identity (e.g., login, password)
  - Prove that one is from the list of allowed countries/states without revealing from which one exactly
  - Prove that one owns a monthly pass to a subway/metro without revealing card's id

- **Anonymous payments**:

  - Payment with full detachment from any kind of identity
  - Paying taxes without revealing one's earnings

- **Outsourcing computation**:
  - Outsource an expensive computation and validate that the result is correct without redoing the execution;
    it opens up a category of trustless computing
  - Changing a blockchain model from everyone computes the same to one party computes and everyone verifies

The idea behind this post is to give a general overview of Zero-Knowledge Proofs,
while providing further resources,
especially which papers to read,
to dive deeper into the subject.
As always, I'll try to keep it simple and intuitive.
However, as you might guess, the subject is quite complex,
and I'll try to simplify it as much as possible;
but some mathematical background is necessary.

## What are ZKPs?

Let's formalize the concept of **Zero-Knowledge Proofs**.
A formal definition of zero-knowledge has to use some computational model,
and without loss of generality,
we can use the [Turing Machine](https://en.wikipedia.org/wiki/Turing_machine)
model.
So let's create three Turing machines:

- $P$ (the **prover**),
- $V$ (the **verifier**),
- and $S$ (the **simulator**).

Let's also spicy things up a bit and introduce an **adversary** $A$,
and assume that it is also a Turing machine.
**The secret we want to prove knowledge without revealing is $x$**.

The prover $P$ wants to prove to the verifier $V$ that it knows the secret $x$.
They both share a common simulator $S$.
The adversary $A$ is trying to fool the verifier $V$ into believing that it knows the secret $x$,
without actually knowing it.

The prover $P$ generates a proof $\pi = P(S, x)$,
and sends it to the verifier $V$.
The verifier $V$ then checks the proof $\pi$,
and decides whether to accept or reject it.

The tuple $(P, V, S)$ is a **Zero-Knowledge Proof** if the following properties hold:

1. **Completeness**: If the statement is true, the verifier will accept the proof.

   $$ \Pr\big[V(S, \pi) = \text{accept} \big] = 1. $$

   Here $\Pr\big[V(S, \pi) = \text{accept} \big]$ denotes the probability that the verifier accepts the proof given a simulator $S$ and a proof $\pi$.

1. **Soundness**: If the statement is true, no cheating prover can convince an honest verifier that it is true,
   except with some negligible probability [^negligible].

   $$ \forall A, \forall x, \forall \pi: \Pr\big[V(A, S, \pi) = \text{accept} \big] < \text{negligible}. $$

   Here $\Pr\big[V(A, S, \pi) = \text{accept} \big]$ denotes the probability that the verifier accepts the proof given an adversary $A$, a simulator $S$, and a proof $\pi$.

1. **Zero-Knowledge**: If the statement is true, the verifier learns nothing about the secret $x$.
   A proof is zero-knowledge if there exists a simulator $S$ that can simulate the verifier's view
   without knowing the secret $x$.

   $$ \forall x: \text{View}\_V\big[P(x) \leftrightarrow V(\pi)\big] = S(x, \pi). $$

   Here $\text{View}_V$ is the view of the verifier $V$,
   and $\leftrightarrow$ denotes the interaction between the prover and the verifier.

> [](<$block.attrs('info')>)
> A function $f$ is negligible if for every polynomial $p$,
> there exists an $N$ such that for all $n > N$,
> $$ f(n) < \frac{1}{p(n)}. $$
> If you want to learn more about negligible functions,
> read Chapter 3, Section 3.1 of the book [Introduction to Modern Cryptography](https://doi.org/10.1201/9781420010756) by Katz & Lindell.

If you come up from a scheme that satisfies these properties,
congratulations, you have a **Zero-Knowledge Proof** scheme
and you can name it whatever you want,
just like a Pokemon!

## ZKPs Taxonomy

We can classify **Zero-Knowledge Proofs** into two broad categories:

1. **Interactive Zero-Knowledge Proofs**: In this case, the prover and the verifier interact multiple times.
   The prover sends a proof to the verifier,
   and the verifier sends a challenge to the prover,
   and this interaction continues until the verifier is convinced.
   The Fiat-Shamir Heuristic can transform an interactive ZKP into a non-interactive ZKP.

1. **Non-Interactive Zero-Knowledge Proofs**: In this case, the prover sends a proof to the verifier,
   and the verifier accepts or rejects the proof.
   No further interaction is needed.

Additionally,
the setup of the **simulator $S$ with respect to the data it uses**
can be further classified into three categories.
Generally speaking, the data used by $S$ is some random bits.
In trusted setups, if the data is compromised,
the security of the proof is also compromised.
In other words, anyone with the hold of the data can prove anything to anyone.
This is bad, and we want to avoid it.

1. **Trusted Setup**: $S$ uses data that must be kept secret.
1. **Trusted but Universal Setup**: $S$ uses data that must be kept private,
   but it only uses for the initial setup.
   Future proofs can be verified without the need for the initial data,
   and can be considered transparent.
1. **Transparent Setup**: $S$ uses no data at all.
   This is the best setup, as it doesn't require any data to be used by $S$.

Some of the most popular Zero-Knowledge Proof systems are:

- **zk-SNARKs**: Zero-Knowledge Succinct Non-Interactive Argument of Knowledge.
  This is a non-interactive ZKP system with a trusted setup.
- **Bulletproofs**: A non-interactive ZKP system with a transparent setup.
- **zk-STARKs**: Zero-Knowledge Scalable Transparent Argument of Knowledge.
  This is a non-interactive ZKP system with a transparent setup,
  with an additional property of being (plausibly) post-quantum secure.

## zk-SNARKs

**zk-SNARKs** are the most popular Zero-Knowledge Proof system.
They are used in the Zcash protocol,
and the defunct Tornado Cash smart contract.
Ethereum also uses zk-SNARKs in its Layer 2 scaling solution,
the zk-Rollups.
[BitVM](https://bitvm.org/) also uses a SNARK-based VM to run smart contracts
on top of Bitcoin.

Let's go over the concepts behind zk-SNARKs.

> [](<$block.attrs('info')>)
> most of this section is based on [Petkus19].

### The first idea: Proving Knowledge of a Polynomial

First some polynomial primer.
**A polynomial $f(x)$ is a function that can be written as**:

$$ f(x) = c_d x^d + \ldots + c_1 x^1 + c_0 x^0 $$

where $c_d, \ldots, c_1, c_0$ are the coefficients of the polynomial,
and $d$ is the degree of the polynomial.

Now, the [Fundamental Theorem of Algebra](https://en.wikipedia.org/wiki/Fundamental_theorem_of_algebra) states that
**a polynomial of degree $d$ can have at most $d$ (real-valued-only) roots**.

> [](<$block.attrs('info')>)
> The "at most" is because we are talking about real-valued-only roots.
> If we consider complex roots, then a polynomial of degree $d$ has exactly $d$ roots.

This can be extended to the concept that **two non-equal polynomials of degree $d$ can have at most $d$ points of intersection**.

The idea of proving knowledge of a polynomial is to show that you know the polynomial,
without revealing the polynomial itself.

This simple protocol can be done in four steps,
note that both the prover and the verifier have knowledge of the polynomial:

1. Verifier chooses a random value for $x$ and evaluates his polynomial locally
1. Verifier gives $x$ to the prover and asks to evaluate the polynomial in question
1. Prover evaluates his polynomial at $x$ and gives the result to the verifier
1. Verifier checks if the local result is equal to the prover's result,
   and if so then the statement is proven with a high confidence

How much is "high confidence"?
Suppose that the verifier chooses an $x$ at random from a set of $2^{256}$ values,
that is a 256-bit number.
According to [Wolfram Alpha](https://www.wolframalpha.com/input?i2d=true&i=Power%5B2%2C256%5D),
the decimal approximation is $\approx 1.16 \times 10^{77}$.
This is almost the [number of atoms in the observable universe](https://en.wikipedia.org/wiki/Observable_universe#Matter_content%E2%80%94number_of_atoms)!
The number of points where evaluations are different is $10^{77} - d$,
where $d$ is the degree of the polynomial.
Therefore, we can assume with overwhelming probability that the prover knows the polynomial.
This is due to the fact that an adversary has $\frac{d}{10^{77}}$ chance of guessing the polynomial[^birthday],
which we can safely consider negligible.

> [](<$block.attrs('info')>)
> The [Birthday paradox](https://en.wikipedia.org/wiki/Birthday_problem)
> states that any collision resistance scheme has a probability of $\frac{1}{2}$ of collision,
> hence we take the square root of the number of possible values.
> So, the security of the polynomial proof is $\sqrt{10^{77}} = 10^{38.5}$,
> which is still a huge number.

### The second idea: Proving Knowledge of a Polynomial without Revealing the Polynomial

The protocol above has some implications,
mainly that the protocol works only for a certain polynomial,
and the verifier has to know the polynomial in advance.
Which is not practical at all since we want to prove knowledge
of a secret without revealing the secret itself.

We can do better, we can use the fact,
also stated in the [Fundamental Theorem of Algebra](https://en.wikipedia.org/wiki/Fundamental_theorem_of_algebra),
that any polynomial can be factored into linear polynomials,
i.e. a set of degree-1 polynomials representing a line.
We can represent any valid polynomial as a product of its linear-polynomial factors:

$$ (x - a_0) (x - a_1) \ldots (x - a_d) = 0 $$

where $a_0, \ldots, a_{d}$ are the roots of the polynomial.
If you wanna prove knowledge of a polynomial, it is just a matter of proving knowledge of its roots.
But how do we do that without disclosing the polynomial itself?
This can be accomplished by proving that a polynomial $p(x)$ is the multiplication
of the factors $t(x) = (x - a_0) \ldots (x - a_d)$, called the **target polynomial**,
and some arbitrary polynomial $h(x)$, called the **residual polynomial**:

$$ p(x) = t(x) \cdot h(x). $$

The prover can show that exists some polynomial $h(x)$ such that
$p(x)$ can be made equal to $t(x)$.
You can find $h(x)$ by simply dividing $p(x)$ by $t(x)$:

$$ h(x) = \frac{p(x)}{t(x)}. $$

Now we can create a protocol that can work for any polynomial $p(x)$
with only three steps:

1. Verifier samples a random value $r$, calculates $t = t(r)$ and gives $r$ to the
   prover
1. Prover calculates $h(x) = \frac{p(x)}{t(x)}$ and evaluates $p = p(r)$ and $h = h(r)$;
   the resulting values $p$, $h$ are provided to the verifier
1. Verifier then checks that $p = t \cdot h$, if so those polynomials are equal,
   meaning that $p(x)$ has $t(x)$ as a cofactor.

Note that the verifier has no clue about the polynomial $p(x)$,
and can be convinced that the prover knows the polynomial $p(x)$.

For example, let's consider two polynomials $p(x)$ and $t(x)$ of degree $3$:

- $p(x) = x^3 - 3x^2 + 2x$
- $t(x) = (x - 1) (x - 2)$

An example protocol interaction in this case could be:

1. Verifier samples a random value $23$, calculates $t = t(23) = (23 − 1)(23 − 2) = 462$ and
   gives $23$ to the prover
1. Prover calculates $h(x) = \frac{p(x)}{t(x)} = x$, evaluates $p = p(23) = 10626$ and $h = h(23) = 23$
   and provides $p$, $h$ to the verifier
1. Verifier then checks that $p = t \cdot h$, i.e. $10626 = 462 \cdot 23$,
   which is true, and therefore the statement is proven

Great! We can prove stuff without revealing the stuff itself!
Noice!
We know only need to find a trick to represent
any sort of computation as a polynomial.

### The third idea: Representing Computations as Polynomials

We can **represent any computation as a polynomial by using [Arithmetic Circuits](https://en.wikipedia.org/wiki/Arithmetic_circuit)**.
An arithmetic circuit is a directed acyclic graph (DAG) where:

- Every indegree-zero node is an input gate that represents a variable $x_i$
- Every node with indegree $>1$ is either:
  - an addition gate, $+$, that represents the sum of its children
  - a multiplication gate, $\times$, that represents the product of its children

Here's an example of an arithmetic circuit that represents the polynomial $p(x_1, x_2) = x_2^3 + x_1 x_2^2 + x_2^2 + x_1 x_2$:

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

The idea is to prove that the output of the circuit is equal to some target polynomial $t(x)$.
This can be done by proving that the output of the circuit is equal to the target polynomial $t(x)$
multiplied by some arbitrary polynomial $h(x)$,
as we did in the previous section.

## Remarks

This is a very high-level overview of Zero-Knowledge Proofs.
The subject is quite complex and requires a lot of mathematical background.
I tried to simplify it as much as possible,
to give a general intuition of how Zero-Knowledge Proofs work.
Please check the resources below for more in-depth information.

## Resources

{% admonition(type="info", icon="info", title="Info") %}
We have tons of papers on the subject.
Here are some selected few.
{% end %}

The whole idea of ZKPs as discussed above in three properties
(Completeness, Soundness, and Zero-Knowledge)
was first conceived by `SMR85`.
Later `Kil92` showed that some of the properties' assumptions can be relaxed,
more specifically using computational soundness instead of statistical soundness.
`Mic94` applied the [Fiat-Shamir Heuristic](https://en.wikipedia.org/wiki/Fiat%E2%80%93Shamir_heuristic)
to `Kil92`'s contributions to show that you can create any non-interactive ZKP system into
a non-interactive ZKP system using the [Random Oracle Model](https://en.wikipedia.org/wiki/Random_oracle_model).

Going to the zk-SNARKs side,
the term was introduced by `Bit11`
and the first protocol, the Pinocchio protocol,
was introduced by `Gen12` and `Par13`.
The Bulletproofs protocol was introduced by `Bunz18`,
followed by the Bulletproofs++ protocol by `Eagen24`.

zk-STARKs were introduced by `Ben-Sasson19`.

Finally, if you want an intuitive but very comprehensive explanation of zk-SNARKs,
then you should read `Petkus19`.

The [Blockchain Web3 MOOC from Berkeley University](https://rdi.berkeley.edu/)
provides a good introduction to Zero-Knowledge Proofs,
while being quite accessible to beginners.

This [video from YouTube](https://youtu.be/iRQw2RpQAVc)
explains the math behind the Arithmetic Circuits
and how to encode them as polynomials.

## References

{% references() %}
`SMR85`: <https://epubs.siam.org/doi/10.1137/0218012> "Goldwasser, S., Micali, S., & Rackoff, C. (1985). The knowledge complexity of interactive proof systems. SIAM Journal on computing, 18(1), 186-208."

`Kil92`: <https://dl.acm.org/doi/abs/10.1145/129712.129782> "Kilian, J. (1992). A note on efficient zero-knowledge proofs and arguments (extended abstract). In Proceedings of the twenty-fourth annual ACM symposium on Theory of computing (pp. 723-732)."

`Mic94`: <https://ieeexplore.ieee.org/abstract/document/365746/> "Micali, S. (1994). CS proofs (extended abstract). In Proceedings 35th Annual Symposium on Foundations of Computer Science (pp. 436-445)."

`Bit11`: <https://eprint.iacr.org/2011/443> "Bitansky, N., Canetti, R., & Goldwasser, S. (2011). From Extractable Collision Resistance to Succinct Non-Interactive Arguments of Knowledge, and Back Again. In Proceedings of the 3rd innovations in theoretical computer science conference (pp. 326-349)."

`Gen12`: <https://eprint.iacr.org/2012/215> "Gennaro, R., Gentry, C., Parno, B., & Raykova, M. (2013). Quadratic span programs and succinct NIZKs without PCPs. In Advances in Cryptology–EUROCRYPT 2013: 32nd Annual International Conference on the Theory and Applications of Cryptographic Techniques, Athens, Greece, May 26-30, 2013. Proceedings 32 (pp. 626-645)."

`Par13`: <https://eprint.iacr.org/2013/279> "Parno, B., Gentry, C., Howell, J., & Raykova, M. (2013). Pinocchio: Nearly practical verifiable computation. In Proceedings of the 2013 IEEE Symposium on Security and Privacy (SP) (pp. 238-252)."

`Bunz18`: <https://ieeexplore.ieee.org/document/8418611> "Bünz, B., Bootle, J., Boneh, D., Poelstra, A., Wuille, P., & Maxwell, G. (2018). Bulletproofs: Short Proofs for Confidential Transactions and More. In Proceedings of the 2018 IEEE Symposium on Security and Privacy (SP) (pp. 315-334)."

`Eagen24`: <https://link.springer.com/chapter/10.1007/978-3-031-58740-5_9> "Bulletproofs++: next generation confidential transactions via reciprocal set membership arguments. In Annual International Conference on the Theory and Applications of Cryptographic Techniques (pp. 249-279)."

`Ben-Sasson19`: <https://link.springer.com/chapter/10.1007/978-3-030-26954-8_23> "Ben-Sasson, E., Bentov, I., Horesh, Y., & Riabzev, M. (2019). Scalable zero knowledge with no trusted setup. In Advances in Cryptology–CRYPTO 2019: 39th Annual International Cryptology Conference, Santa Barbara, CA, USA, August 18–22, 2019, Proceedings, Part III 39 (pp. 701-732)."

`Petkus19`: <https://arxiv.org/abs/1906.07221> "Petkus, M. (2019). Why and How zk-SNARK works. arXiv preprint 1906.07221."
{% end %}
