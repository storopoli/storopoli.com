---
title: The beauty of math's incompleteness or how self-references can beautifully screw things up
date: 2025-05-24
author: Jose Storopoli
description: How I've fell in love with Math.
tags: [math, agda]
---

![A curios mathematician seeing a blackhole of self-referential paradoxes.](/images/self-referential-blackhole.png)

> "Logic is the hygiene that the mathematician practises to keep his ideas healthy and strong."
>
> --- Hermann Weyl

I have a very special place for **mathematics in my mind and heart**.

Mathematics is above _any other science_.
This is because the knowledge we gather in all other sciences are never _absolutely true_.
All other sciences are based on observations and experiments,
and eventually evidence accrues to a threshold that we can morally declare that something is _true_.
Yet, it is not _mathematically true_, in other words, for any given pile of evidence about a given hypothesis $H$,
we have $P(H) < 1$.
In a pure philosophical sense, we can never be _absolutely sure_ about scientific hypotheses.
There will always be a certain degree of uncertainty even if we have a lot of evidence in favor of a given hypothesis.
For mathematical theorems, which is the meat of mathematics, once they are proven, they are _absolutely true_,
i.e. $P(H) = 1$.
For example, imagine a galaxy very far away, and a million years from now, given the
[5 axioms of Euclidian geometry](https://en.wikipedia.org/wiki/Euclidean_geometry#Axioms),
the theorem that the sum of the angles of a triangle is 180 degrees will still be true.
It will always be true (given the 5 axioms of course).

That is how mathematics won my mind.
Now, how it won my heart is a different story.
It has to do with the beauty of math's _incompleteness_, _inconsistency_, and _undecidability_.
Which all stems from **self-referential paradoxes**.

## Cantor and multiple infinities

![Georg Cantor](/images/georg-cantor.jpg)

Let's go back to 1874, when [Georg Cantor](https://en.wikipedia.org/wiki/Georg_Cantor)
proved that there are **multiple infinities**.
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
A **bijection** is a function that is one-to-one and onto.
In other words, it is a function that maps each element of the first set to a unique element of the second set,
and each element of the second set to a unique element of the first set.

For example, the function

$$
f(n) = \begin{cases}
    -\frac{n}{2} & \text{if } n \text{ is even} \\
    \frac{n+1}{2} & \text{if } n \text{ is odd}
\end{cases}
$$

is a bijection between the set of natural numbers and the set of integers.

It creates a one-to-one correspondence between the set of natural numbers and the set of integers:

| $f(n)$ | $\mathbb{N}$ | $\mathbb{Z}$ |
|:------:|:------------:|:------------:|
| f(0)   | 0            | 0            |
| f(1)   | 1            | 1            |
| f(2)   | 2            | -1           |
| f(3)   | 3            | 2            |
| f(4)   | 4            | -2           |
| f(5)   | 5            | 3            |
| f(6)   | 6            | -3           |

Ok that was easy, we just proved that the **set of natural numbers and the set of integers have the same size**.
Now let's try to prove the same for the set of rational numbers $\mathbb{Q}$.
The idea again is to find a bijection between the set of natural numbers and the set of rational numbers.
We can represent the set of rational numbers as a grid of fractions:

$$
\begin{array}{cccc}
    \frac{1}{1} & \quad \frac{1}{2} & \quad \frac{1}{3} & \quad \cdots \\\\
    \frac{2}{1} & \quad \frac{2}{2} & \quad \frac{2}{3} & \quad \cdots \\\\
    \frac{3}{1} & \quad \frac{3}{2} & \quad \frac{3}{3} & \quad \cdots \\\\
    \vdots & \quad \vdots & \quad \vdots & \quad \ddots \\\\
\end{array}
$$

Now, we can't just go row by row or column by column --- that would never finish the first row!
Instead, Cantor had a brilliant idea: traverse the grid diagonally in a zigzag pattern[^pairing-function].

[^pairing-function]: {-} This is called a [**pairing function**](https://en.wikipedia.org/wiki/Pairing_function),
  and specifically the [**Cantor pairing function**](https://en.wikipedia.org/wiki/Cantor_pairing_function).

$$
\begin{array}{cccccccc}
    \frac{1}{1} & \rightarrow & \frac{1}{2} & \quad & \frac{1}{3} & \rightarrow & \frac{1}{4} & \cdots \\
    & \swarrow & & \nearrow & & \swarrow & \\
    \frac{2}{1} & & \frac{2}{2} & & \frac{2}{3} & & \frac{2}{4} & \cdots \\
    \downarrow & \nearrow & & \swarrow & & & \\
    \frac{3}{1} & & \frac{3}{2} & & \frac{3}{3} & & \frac{3}{4} & \cdots \\
    & \swarrow & & \nearrow & & & \\
    \frac{4}{1} & & \frac{4}{2} & & \frac{4}{3} & & \frac{4}{4} & \cdots \\
    \vdots & & \vdots & & \vdots & & \vdots & \ddots \\
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

Ok we're almost there.
This is truly a bijection.
However, it is a bijection between $\mathbb{N}$ and the set of _positive rationals_, $\mathbb{Q}^+$.
To include all of $\mathbb{Q}$, we interleave _positive and negative rationals_ (and zero).
I won't give the precise mathematical formula here because it is a bit messy,
however here's an algorithm describing the bijection:

1. Start with $n$
1. If $n = 0$, return $0$
1. Otherwise:

   - Let $k = \frac{n+1}{2}$ if $n$ is odd, $k = \frac{n}{2}$ if $n$ is even
   - Find the $k$-th positive rational in our enumeration, call it $r$
   - If $n$ is odd, return $r$
   - If $n$ is even, return $-r$

This gives us the following bijection:

| $g(n)$ | $\mathbb{N}$ | $\mathbb{Q}^+$ enumeration  | $\mathbb{Q}$   |
|:------:|:------------:|:---------------------------:|:--------------:|
| g(0)   | 0            | -                           | 0              |
| g(1)   | 1            | 1st positive: $\frac{1}{1}$ | 1              |
| g(2)   | 2            | 1st positive: $\frac{1}{1}$ | -1             |
| g(3)   | 3            | 2nd positive: $\frac{1}{2}$ | $\frac{1}{2}$  |
| g(4)   | 4            | 2nd positive: $\frac{1}{2}$ | $-\frac{1}{2}$ |
| g(5)   | 5            | 3rd positive: $\frac{2}{1}$ | 2              |
| g(6)   | 6            | 3rd positive: $\frac{2}{1}$ | -2             |

Q.E.D.! We have a **bijection between $\mathbb{N}$ and $\mathbb{Q}$**.

I went over all of these details because this diagonalization argument is a very important insight.
Any set that can be put in a one-to-one correspondence with the set of natural numbers is called **countable**.
Cantor showed that the set of rational numbers is countable.

Let's see what happens when we try to apply the same argument to the set of real numbers $\mathbb{R}$.
For the sake of simplicity, let's consider the set of real numbers between 0 and 1, $\mathbb{R}_{(0,1)}$.

Let's assume that we have a bijection $f$ between $\mathbb{N}$ and $\mathbb{R}_{(0,1)}$.
This would give us the following table:

| $f(n)$ | $\mathbb{N}$ | $\mathbb{R}_{(0,1)}$ |
|:------:|:------------:|:--------------------:|
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

This is a **contradiction**, since we assumed that $f$ was a bijection.

Now, this is where **self-reference** strikes first in this post,
and probably in the history of mathematics.
When we construct the _diagonal number_ $x$, we're creating something that:

1. Refers to the entire supposed list of real numbers.
1. Defines itself in opposition to that list --- "I differ from the 1st number at position 1, from the 2nd at position 2...".
1. Uses the list to prove the list is incomplete.

Ultimately, this is where Cantor found the first example of a set that is **not countable**.
There's no way to pair the set of natural numbers with the set of real numbers between 0 and 1.
Therefore, the set of real numbers between 0 and 1 is **not countable**.
This is called the [Cantor's diagonal argument](https://en.wikipedia.org/wiki/Cantor%27s_diagonal_argument).

This is a very important insight.
It shows that there are **different sizes of infinity**.
Yes, that is mind-blowing and paradoxically beautiful.

Cantor called the size of the set of natural numbers $\aleph_0$,
and conjectured that the set of real numbers is $\aleph_1$.
This is called the [**continuum hypothesis**](https://en.wikipedia.org/wiki/Continuum_hypothesis) (CH).

## Russell and the barber paradox

![Bertrand Russell](/images/bertrand-russell.jpg)

Now let's fast forward to 1901.
Set theory was still in its infancy,
yet it was starting to be accepted by the mathematical community.
This is where [Bertrand Russell](https://en.wikipedia.org/wiki/Bertrand_Russell)
after attending the first [World Congress of Philosophy](https://en.wikipedia.org/wiki/World_Congress_of_Philosophy) in Paris in 1900,
was impressed by the work of Peano who was using set theory to formalize mathematics.

He embarked on a journey to **formalize mathematics using set theory**.
However, he stumbled upon a **paradox**.
Set theory is very lenient with the definition of sets.
For example, we can define the set of all sets that are **not members of themselves**:

$$
R = \{ x \mid x \notin x \}
$$

Now what happens if we ask the question: **is $R$ a member of itself?**
If $R$ is a member of itself, then it is _not_ a member of itself.
If $R$ is _not_ a member of itself, then it is a member of itself.

To put more simply, Russell gave the simple analogy:
imagine a barber who shaves all men who do not shave themselves.
Now, the question is: **does the barber shave himself?**
If he does, then he does _not_ shave himself.
If he does _not_ shave himself, then he does shave himself.

I can even given an even more simple example: the statement "this statement is false" is a paradox.
If it is true, then it is false.
If it is false, then it is true.

Or suppose that I go out and shout out loud: "I am lying".
If I am lying, then I am _not_ lying.
If I am _not_ lying, then I am lying.

All of these examples boil down to the same thing:
we cannot have a set of all sets that are **not members of themselves**.

This is called the [**Russell's paradox**](https://en.wikipedia.org/wiki/Russell%27s_paradox).
And yet again, we have **self-reference** creating a paradox.
Personally, I find Cantor's multiple infinities more beautiful than Russell's paradox.
But I acknowledge that Russell's paradox is way simpler and more accessible to the general public.

## Turing and computation

![Alan Turing](/images/alan-turing.jpg)

Before we dive into Gödel's earth-shattering results,
let's take a step back and understand a simpler but equally profound concept
that will make everything else crystal clear: **computation** and **Turing machines**.

In 1900 during the second
[International Congress of Mathematicians](https://en.wikipedia.org/wiki/International_Congress_of_Mathematicians)
in Paris, [David Hilbert](https://en.wikipedia.org/wiki/David_Hilbert)
posed three fundamental questions about mathematics:

1. **Was mathematics complete?** (Can every true statement be proven?)
1. **Was mathematics consistent?** (Can we avoid contradictions?)
1. **Was mathematics decidable?** (Is there an algorithm to determine if any statement is true?)

Gödel would shatter the first two dreams in 1931.
But the third question, [the **Entscheidungsproblem** ("decision problem"),
also known as the **halting problem**](https://en.wikipedia.org/wiki/Halting_problem),
remained tantalizingly open.
Could there be a mechanical procedure to decide the truth of any mathematical statement?

Alan Turing, in 1936, while still an undergraduate at King's College, Cambridge,
would answer this question with a resounding **no**.
But to do so, he first had to define what "mechanical procedure" even meant.

### The Turing machine: the essence of computation

Turing introduced the concept of the [**Turing machine**](https://en.wikipedia.org/wiki/Turing_machine) ---
a simple but powerful mathematical model of computation.
A Turing machine consists of:

1. **An infinite tape** divided into cells, each containing a symbol (usually 0, 1, or blank)
1. **A read/write head** that can scan one cell at a time
1. **A finite set of states** that control the machine's behavior
1. **A transition function** that, given the current state and symbol, determines:

   - What symbol to write
   - Whether to move left or right
   - What state to enter next

Here's a simple example --- a Turing machine that adds 1 to a binary number:

```
Input tape:  ...□ 1 0 1 1 □...
             Start here ↑

States:
- q₀: "scanning right, looking for the end"
- q₁: "found end, now carrying"
- qf: "finished"

Rules:
- (q₀, 0) → (q₀, 0, R)  # Keep scanning right
- (q₀, 1) → (q₀, 1, R)  # Keep scanning right
- (q₀, □) → (q₁, □, L)  # Found end, go back left
- (q₁, 0) → (qf, 1, R)  # 0+1=1, done
- (q₁, 1) → (q₁, 0, L)  # 1+1=0, carry left
```

The beauty of Turing machines is their **universality** --- despite their simplicity,
they can compute anything that any computer can compute.
This is the [**Church-Turing thesis**](https://en.wikipedia.org/wiki/Church–Turing_thesis):
anything we intuitively consider "computable" can be computed by a Turing machine.

### Programs as data: the key insight

Here's where things get interesting. Since Turing machines follow simple rules,
we can **encode any Turing machine as a string of symbols**.
Just assign numbers to states and symbols:

- State $q_0 \rightarrow 1$
- State $q_1 \rightarrow 2$
- Symbol $0 \rightarrow 1$
- Symbol $1 \rightarrow 2$
- Move Left $\rightarrow 1$
- Move Right $\rightarrow 2$

Now our entire machine becomes a sequence of numbers, which we can write on a tape!

This means we can build an [**Universal Turing Machine**](https://en.wikipedia.org/wiki/Universal_Turing_machine) (UTM) that:

1. Takes as input the encoding of any Turing machine M
1. Takes as input some data D
1. Simulates what M would do when run on D

In other words: **programs become data**.
This is the fundamental insight behind modern computers ---
we can write programs that manipulate other programs.

### The halting problem: when self-reference strikes

Now comes the million-dollar question:
given a Turing machine $M$ and input $I$,
can we determine **whether $M$ will eventually halt (stop) when run on $I$,
or will it run forever?**

This is called the [**halting problem**](https://en.wikipedia.org/wiki/Halting_problem),
and Turing proved it's **undecidable**.

The proof is a masterpiece of self-reference.
It is a [**proof by contradiction**](https://en.wikipedia.org/wiki/Proof_by_contradiction),
where we assume that something is true and we derive a contradiction.
This allows us to disprove the initial assumption.

Suppose we have a magical Turing machine `halts` that solves the halting problem.
Here’s how the function signature looks like in Haskell notation:

```haskell
halts :: TuringMachine -> Input -> Bool
```

The machine will output `True` if the machine halts and `False` if it runs forever.

Now, let's construct a diabolical machine `diagonal`:

```haskell
diagonal :: TuringMachine -> ()
diagonal m = if halts m m  -- Note: m is used as both machine AND input
             then loop     -- Run forever
             else ()       -- Halt immediately
  where
    loop = loop            -- Infinite recursion
```

The key insight is that `diagonal` takes a Turing machine `m`
and **uses `m` as both the machine and the input** to `halts`.
Then:

- If `halts m m` returns `True`
  (meaning machine `m` halts when run on itself), then `diagonal`
  enters an infinite loop
- If `halts m m` returns `False`
  (meaning machine `m` runs forever on itself), then `diagonal`
  halts immediately by returning `()`

Now comes the crucial question:
**What happens when we run `diagonal diagonal`?**

Let's trace through both possibilities:

- **Case 1**: Suppose `halts diagonal diagonal = True`

  - This means `diagonal` halts when run on itself
  - But by definition, if `halts diagonal diagonal = True`, then `diagonal diagonal` executes the `loop` branch
  - So `diagonal diagonal` runs forever!
  - Contradiction: we assumed it halts, but it actually loops ❌

- **Case 2**: Suppose `halts diagonal diagonal = False`
  - This means `diagonal` runs forever when run on itself
  - But by definition, if `halts diagonal diagonal = False`, then `diagonal diagonal` executes the `()` branch
  - So `diagonal diagonal` halts immediately!
  - Contradiction: we assumed it loops, but it actually halts ❌

Since both cases lead to contradiction,
our assumption is false.
**No such machine `halts` can exist!**

Thus, the halting problem is **undecidable**!

That's how Turing, at the young age of 24,
proved that **mathematics is _not_ decidable**.

### The deeper pattern: diagonalization everywhere

Notice the beautiful pattern emerging:

1. **Cantor**: Construct a real number that differs from every number in any proposed list
2. **Russell**: Ask whether the set of "sets that don't contain themselves" contains itself
3. **Turing**: Build a machine that does the opposite of what a hypothetical "halting detector" predicts

All use the same technique: **diagonalization with self-reference**. We construct an object that:

1. Refers to an entire collection (reals, sets, machines)
1. Defines itself in opposition to that collection
1. Creates a contradiction that proves the collection is impossible

This is the **universal pattern** underlying all of mathematics' most profound limitations.

## Gödel through Turing's lens

![Kurt Gödel](/images/kurt-godel.jpg)

Now that we understand Turing machines and the halting problem,
Gödel's incompleteness theorems become much clearer.
In fact, Gödel himself later said that using Turing machines was the "right way" to prove his theorems!

Hilbert's three questions were:

1. **Completeness**: Can every true statement be proven?
1. **Consistency**: Can we avoid contradictions?
1. **Decidability**: Can we mechanically determine if any statement is true?

Turing answered #3 with a definitive **no**.
Gödel answered #1 and #2 by showing they're incompatible ---
we can have consistency **or** completeness,
but not both.

### From halting to incompleteness

Here's the key insight: **mathematical proof-checking is a computational process**.

Given a mathematical statement $S$ and a purported proof $P$,
we can write a Turing machine that:

1. Checks if $P$ follows valid logical rules
1. Verifies each step is correct
1. Confirms $P$ actually proves $S$
1. Halts with "VALID" or "INVALID"

This means **provability becomes a computational question**.

### The first theorem: Gödel's incompleteness theorem

The genius of Gödel's approach becomes crystal clear when viewed through Turing machines.
Since mathematical proof-checking is computational,
we can treat every mathematical statement as a string
that a Turing machine can process[^godel-numbering].

[^godel-numbering]:
  {-} Gödel's original approach used a clever [**numbering system**](https://en.wikipedia.org/wiki/Gödel_numbering)
  that assigned unique natural numbers to mathematical symbols and formulas,
  allowing statements about formulas to become statements about numbers.
  While ingenious, this encoding obscures the essential insight that computation provides more directly.

Now imagine building a "proof searcher" machine `PROVE(S)` that systematically generates all possible proofs,
checks if any proof establishes statement $S$,
and halts if it finds one (running forever if no proof exists).

With this setup,
Gödel constructs his famous sentence $G$ that essentially says:
**"This statement cannot be proven by any Turing machine"**[^statement]

[^statement]:
  {-} More precisely:
  "There is no Turing machine that halts and outputs a valid proof of this statement".

The self-reference paradox unfolds beautifully.
If $G$ is provable,
then some machine finds a proof and halts ---
but this makes $G$ false,
since $G$ claims no machine can prove it.
So we've proven a false statement, making our system inconsistent!

Conversely, if $G$ is not provable, then no machine can indeed prove it ---
making $G$ true, since it correctly states its own unprovability.
But now we have a true statement that can't be proven, making our system incomplete!

The devastating conclusion:
**Any consistent formal system strong enough to discuss Turing machines must be incomplete**.
Truth and provability are fundamentally different concepts.

### The second theorem: arithmetic cannot validate itself

Why does **arithmetic matter so much?**
Because arithmetic --- just addition, multiplication,
and basic properties of natural numbers --- forms the foundation of all mathematics.
Every mathematical structure ultimately relies on counting and basic numerical relationships.
**If arithmetic fails, everything built on top of it collapses**.

The Second Incompleteness Theorem delivers the devastating result:
**"Arithmetic cannot prove its own consistency"**.

The proof is a masterful application of the first theorem. Let's break it down step by step.

Recall that our Gödel sentence $G$ says:
"This statement ($G$) cannot be proven in arithmetic".
From the first theorem, we learned that if arithmetic is consistent,
then $G$ is indeed unprovable (because if $G$ were provable, we'd have a contradiction).

Now here's the key insight:
arithmetic itself can prove this logical relationship!
That is, arithmetic can prove the statement:
"If arithmetic is consistent, then $G$ is unprovable".

Why can arithmetic prove this?
Because the first incompleteness theorem's proof can be formalized within arithmetic itself.
Arithmetic can "see" that assuming its own consistency leads to $G$ being unprovable.

Now suppose arithmetic could also prove its own consistency ---
call this statement Cons(Arithmetic).
Then we'd have:

1. Arithmetic proves: Cons(Arithmetic)
1. Arithmetic proves: "If Cons(Arithmetic), then $G$ is unprovable"
1. By modus ponens: Arithmetic proves "$G$ is unprovable"

But wait!
If arithmetic can prove that "$G$ is unprovable",
then arithmetic knows $G$ is true
(since $G$ says exactly that --- it cannot be proven).
And if arithmetic knows $G$ is true in a consistent system,
it should be able to prove $G$.

This creates the contradiction:
arithmetic both proves that $G$ is unprovable AND should be able to prove $G$ itself.

The only way to avoid this contradiction is if arithmetic cannot prove Cons(Arithmetic) in the first place.

The profound implication: **Mathematics cannot certify its own reliability from within**.
We must take arithmetic's consistency on faith ---
there's no internal proof that it won't one day derive both
"$2+2 = 4$" and "$2+2 \ne 4$".
Any proof of consistency must come from a stronger system outside arithmetic itself,
but then we face the same problem for that stronger system.

## Agda proof that the set of real numbers is uncountable

[**Agda**](https://agda.readthedocs.io/) is a dependently typed programming language.
It is often used to prove mathematical theorems.
But you can also compile it to Haskell using GHC or to JavaScript using a native compiler.
It is like Haskell on steroids,
some call it ["**Super Haskell**"](https://youtu.be/OSDgVxdP20g).

It follows very closely the [**Curry-Howard correspondence**](https://en.wikipedia.org/wiki/Curry%E2%80%93Howard_correspondence),
which is a **magnificent connection between logic and programming**.
People also called it "**proof-as-program**" or "**programs-as-proofs**",
since it is a one-to-one correspondence between programs and proofs.
The basic idea is that you can write a program that proves a theorem,
and the program will type-check if the theorem is true.
This is done by having a very powerful and expressive type system,
that allows you to express the properties of the objects you are working with.
If a type is "inhabited", it means that there exists a term/value of that type,
which under Curry-Howard corresponds to having a proof of the proposition that the type represents.

So when a type is "_inhabited_" in Agda, it means:

- You can construct a value of that type --- there exists some term `t : T`.
- The corresponding logical proposition is true/provable.
- You have evidence/proof of that proposition.

Here are some Agda types and their corresponding logical propositions:

- `⊥` (bottom type) is uninhabited --- corresponds to `False` (no proof possible).
- `⊤` (unit type) is inhabited by `tt` --- corresponds to trivially `True`.
- `A → B` (implication type) is inhabited by a function --- corresponds to `A` implies `B` being provable.
  This is called the [Function type](https://agda.readthedocs.io/en/stable/language/function-types.html)
  in Agda.
  For example, the type of the addition function for natural numbers is:

  ```agda
  Nat → Nat → Nat
  ```

- `A × B` (product type) is inhabited by a pair `a , b` --- corresponds to `A` and `B` both being true.
  For example, the type of a pair of natural numbers is:

  ```agda
  Nat × Nat
  ```

- `A ⊎ B` (sum type) is inhabited by `inj₁ a` or `inj₂ b` --- corresponds to `A` or `B` being true.
   Note that `⊎` is the symbol for disjunction.
   For example, the type of a natural number or a boolean is:

   ```agda
   Nat ⊎ Bool
   ```

- `Σ[ x ∈ A ] B x` (dependent sum type) is inhabited by a pair `a , b` --- corresponds to "there exists `x : A` such that `B x` is true".
   Note that [`Σ` type](https://agda.readthedocs.io/en/stable/language/built-ins.html#the-type) is the same as the [dependent pair type](https://en.wikipedia.org/wiki/Dependent_type) in type theory.
   This is more tricky than the product type, because the type of the second component depends on the value of the first component.

   For example, consider a pair where the first component is a boolean and the second component's type depends on that boolean:

   ```agda
   BoolDependent : Bool → Set
   BoolDependent true  = ℕ      -- If true, second component is a natural number
   BoolDependent false = String -- If false, second component is a string

   -- The dependent sum type:
   BoolDependentPair : Set
   BoolDependentPair = Σ[ b ∈ Bool ] BoolDependent b
   ```

   A value of this type could be `true , 42` (boolean true paired with natural number 42) or `false , "hello"` (boolean false paired with string "hello").
   The type of the second component depends on the value of the first component.

- `A ≡ B` (equality type) is inhabited by a proof of `A` being equal to `B` --- corresponds to `A` and `B` being the same.
   Note that `≡` is the symbol for equality.

   For example, we can prove that `2 + 2 ≡ 4`:

   ```agda
   proof-2+2=4 : 2 + 2 ≡ 4
   proof-2+2=4 = refl
   ```

   Here `refl` (reflexivity) is the constructor that proves any term is equal to itself.
   Since `2 + 2` evaluates to `4` definitionally in Agda,
   we can use `refl` to prove they are equal. The type `2 + 2 ≡ 4` is inhabited by the proof `refl`,
   which serves as evidence that this equality holds.

To learn Agda, a really nice resource is not only the [**Agda documentation**](https://agda.readthedocs.io/),
but also the [**Certainty by Construction: Software and Mathematics in Agda**](https://leanpub.com/certainty-by-construction)
book by Sandy Maguire.

I also suggest this quick introduction to Agda:

<style>
  .embed-container {
    position: relative;
    padding-bottom: 56.25%;
    height: 0;
    overflow: hidden;
    max-width: 100%;
  }
  .embed-container iframe,
  .embed-container object,
  .embed-container embed {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }
</style>
<div class="embed-container">
  <iframe
    src="https://www.youtube.com/embed/OSDgVxdP20g"
    frameborder="0"
    allowfullscreen
  ></iframe>
</div>

Now, let's prove that the **set of real numbers is _uncountable_**.
I'm gonna dump the whole Agda code here,
then explain the parts that are not obvious.
To run the code (which is the same as proving the code or theorem, since the code is the theorem, a.k.a Curry-Howard correspondence),
dump the code into a file named `CantorDiagonalReals.agda`.
You can run the code by installing Agda and running `agda CantorDiagonalReals.agda`.
Agda will silently compile the code and if nothing is printed,
it means the code (and the theorem) is correct (or true).
If you want the Lean version, see the [appendix](#appendix-lean-translation-of-the-agda-proof).

```agda
module CantorDiagonalReals where

open import Data.Nat using (ℕ; zero; suc)
open import Data.Bool using (Bool; true; false)
open import Data.Empty using (⊥)
open import Data.Product using (Σ; _,_; _×_; Σ-syntax)
open import Relation.Binary.PropositionalEquality using (_≡_; refl; cong; trans)
open import Relation.Nullary using (¬_)

-- A real number in (0,1) represented as an infinite sequence of binary digits
Real : Set
Real = ℕ → Bool  -- Each position has a digit 0 or 1


-- Abbreviation for inequality
_≢_ : {A : Set} → A → A → Set
x ≢ y = ¬ (x ≡ y)

-- Helper to flip a bit
flip : Bool → Bool
flip true = false
flip false = true

-- Proof that flip always changes the bit
flip-changes : (b : Bool) → b ≢ flip b
flip-changes true ()
flip-changes false ()

-- The diagonal argument: no enumeration of reals in (0,1) exists
no-enumeration : (f : ℕ → Real) → Σ[ r ∈ Real ] ((n : ℕ) → f n ≢ r)
no-enumeration f = diagonal , proof
  where
    -- Construct the diagonal number by flipping the nth digit of the nth number
    diagonal : Real
    diagonal n = flip (f n n)

    -- Proof that diagonal differs from every f n
    proof : (n : ℕ) → f n ≢ diagonal
    proof n eq = contradiction
      where
        -- If f n = diagonal, then at position n:
        -- (f n n) = (diagonal n) = flip (f n n)
        same-at-n : f n n ≡ diagonal n
        same-at-n = cong (λ r → r n) eq

        -- But diagonal n = flip (f n n) by definition
        diagonal-def : diagonal n ≡ flip (f n n)
        diagonal-def = refl

        -- So f n n = flip (f n n)
        self-eq-flip : f n n ≡ flip (f n n)
        self-eq-flip = trans same-at-n diagonal-def

        -- This contradicts the fact that flip always changes the bit
        contradiction : ⊥
        contradiction = flip-changes (f n n) self-eq-flip
```

Let's break down this proof step by step:

### 1. Real number representation

```agda
Real : Set
Real = ℕ → Bool  -- Each position has a digit 0 or 1
```

We represent real numbers in the interval $(0,1)$ as infinite sequences of binary digits.
This will make the proof easier to follow without losing any generality.
A real number is a function from natural numbers to booleans, where each position gives us a binary digit.

### 2. The flip function

```agda
flip : Bool → Bool
flip true = false
flip false = true

flip-changes : (b : Bool) → b ≢ flip b
flip-changes true ()
flip-changes false ()
```

The `flip` function switches `true` to `false` and vice versa.
The `flip-changes` proof shows that flipping a boolean always produces a different boolean.
The `()` pattern means "impossible case" --- there's no way `true ≡ false` or `false ≡ true`.
It is called the [**absurd pattern**](https://agda.readthedocs.io/en/stable/language/function-definitions.html#absurd-patterns).

### 3. The main theorem

```agda
no-enumeration : (f : ℕ → Real) → Σ[ r ∈ Real ] ((n : ℕ) → f n ≢ r)
```

This says: "For any supposed enumeration `f` of real numbers, there exists a real number `r` that differs from every number in the enumeration."
This is exactly Cantor's **diagonalization argument**!

### 4. The diagonal construction

```agda
diagonal : Real
diagonal n = flip (f n n)
```

We construct our diagonal number by taking the $n$-th digit of the $n$-th number in the enumeration and flipping it.
So `diagonal 0 = flip (f 0 0)`, `diagonal 1 = flip (f 1 1)`, etc.

### 5. The proof of difference

```agda
proof : (n : ℕ) → f n ≢ diagonal
proof n eq = contradiction
```

For any number `f n` in our enumeration, we prove it cannot be equal to our diagonal number.
If they were equal (`eq : f n ≡ diagonal`), we derive a contradiction.

### 6. The contradiction

Now let's examine the contradiction step by step.
We assume we have an equality `eq : f n ≡ diagonal` and derive a contradiction:

```agda
same-at-n : f n n ≡ diagonal n
same-at-n = cong (λ r → r n) eq
```

This uses **congruence** (`cong`) to say: if two functions are equal (`f n ≡ diagonal`),
then applying them to the same argument (`n`) gives equal results.
So `f n n ≡ diagonal n`.

The `λ r → r n` is a **lambda function** (anonymous function) that takes a function `r` and applies it to the argument `n`.
It's like saying "given any function `r`, apply it to `n`".
So `cong (λ r → r n) eq` means: "if `f n ≡ diagonal`,
then applying the operation "apply to `n`" to both sides gives `f n n ≡ diagonal n`".

```agda
diagonal-def : diagonal n ≡ flip (f n n)
diagonal-def = refl
```

This is just the definition of our diagonal function unfolding.
Since `diagonal n = flip (f n n)` by definition,
we can prove this equality with `refl` (reflexivity).

```agda
self-eq-flip : f n n ≡ flip (f n n)
self-eq-flip = trans same-at-n diagonal-def
```

Now we chain the equalities using **transitivity** (`trans`):

- We know `f n n ≡ diagonal n` (from `same-at-n`)
- We know `diagonal n ≡ flip (f n n)` (from `diagonal-def`)
- Therefore `f n n ≡ flip (f n n)` (by transitivity)

But this is **impossible**!
We're saying a boolean equals its own flip.

```agda
contradiction : ⊥
contradiction = flip-changes (f n n) self-eq-flip
```

Finally, we use our `flip-changes` lemma,
which proves that `(b : Bool) → b ≢ flip b`.
Since we have a proof that `f n n ≡ flip (f n n)` (which contradicts `flip-changes`),
we can derive the bottom type `⊥`
(which is uninhabited, so it is false/contradiction).

This elegant proof captures the essence of Cantor's diagonalization:
**we construct a number that systematically differs from every number in any proposed enumeration,
proving that _no such enumeration can exist_**.

## Appendix: Lean translation of the Agda proof

```{.haskell .lean}
namespace CantorDiagonalReals

def Real : Type := Nat → Bool

def bitFlip : Bool → Bool
  | true => false
  | false => true

theorem bitFlip_changes (b : Bool) : b ≠ bitFlip b := by
  cases b <;> decide

theorem no_enumeration (f : Nat → Real) : ∃ r : Real, ∀ n : Nat, f n ≠ r := by
  refine ⟨fun n => bitFlip (f n n), ?_⟩
  intro n eq_fn_r
  have self_eq_flip : f n n = bitFlip (f n n) := by
    simpa using congrFun eq_fn_r n
  exact bitFlip_changes (f n n) self_eq_flip

end CantorDiagonalReals
```

## Conclusion

I hope you enjoyed this journey into the beauty of mathematics.
These self-referential paradoxes underlie the
absurd dichotomy of truth and provability,
while also revealing the profound beauty of mathematics' uncomprehensiveness.

I often think that mathematics is the language of the universe.
Yet, given the incompleteness of mathematics,
will it ever be able to describe the universe?
Or will the universe be engulfed by a mist of forever unknowable mysteries?

Like Hilbert, I am left yelling at the void:
["Wir müssen wissen, wir werden wissen."](https://en.wikipedia.org/wiki/Ignoramus_et_ignorabimus),
which translates to "We must know, we will know."
