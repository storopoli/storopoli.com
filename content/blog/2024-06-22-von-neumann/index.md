+++
title = "Von Neumann: the sharpest mind of the 20th century"
date = "2024-06-22T05:54:46"
author = "Jose Storopoli, PhD"

[taxonomies]
tags = ["math"]

[extra]
katex = true
+++

{{ katex() }}

![Von Neumann's wartime Los Alamos ID badge photo](von_neumann.jpg)

John von Neumann was a Hungarian-American mathematician.
But to define him as a simple mathematician would be an understatement.
He is a **fucking legend** and one of my heroes!
He single-handedly:

- **proposed an axiomatization of [set theory](https://en.wikipedia.org/wiki/Von_Neumann%E2%80%93Bernays%E2%80%93G%C3%B6del_set_theory)**
  along with a definition of [cardinality](https://en.wikipedia.org/wiki/Von_Neumann_cardinal_assignment)
  that remains the standard one in mathematics today.
  Funny enough he started working on solving the paradoxes
  of set theory while he was only 11 years old!
- **laid the mathematical foundations of quantum mechanics**.
- **made the atomic bomb possible** by conceptualizing and designing
  the explosive lenses that were needed to compress the plutonium core
  of the Fat Man weapon that was later dropped on Nagasaki.
  He also invented the term "kiloton" of TNT as a unit of energy
  released in a nuclear explosion.
- **invented the modern computer**. Yes, I know, Alan Turing came up with
  the idea while trying to solve the [halting problem](https://en.wikipedia.org/wiki/Halting_problem),
  but it was von Neumann that recognized the true potential of
  computing machines and designed the first computers.
  We even have the [von Neumann architecture](https://en.wikipedia.org/wiki/Von_Neumann_architecture) that pretty much underlies in every working
  universal Turing machine in the world.
- **created the field of [game theory](https://en.wikipedia.org/wiki/Game_theory)**,
  along with the most important game theory's theorem: the [minimax theorem](https://en.wikipedia.org/wiki/Minimax_theorem).
- **co-invented the [Monte Carlo method](https://en.wikipedia.org/wiki/Monte_Carlo_method)**
  while trying to solve the problem of neutron diffusion.
- **created the field of [cellular automata](https://en.wikipedia.org/wiki/Cellular_automaton)**
  and paved the way for the discovery of DNA.

The list above is just a quick summary of his achievements.
Everywhere you look in mathematics, physics, computer science, and even biology and economics,
you'll find von Neumann's fingerprints.

## The Sharpest Mind of the 20th Century

Von Neumann was recognized by his peers as one of the most intelligent people
to have ever lived.
Johnny, as he was known to his friends, was a prodigy since early childhood.
Some sources suggest that he could multiply two 8-digit numbers together in his head when he was six.
As a child, von Neumann absorbed Ancient Greek and Latin, and spoke French, German and English as well as his native Hungarian.
He devoured a forty-five-volume history of the world and was able to recite whole chapters verbatim decades later.

Here are some quotes from his contemporaries:

- **[Enrico Fermi](https://en.wikipedia.org/wiki/Enrico_Fermi) (Nobel Prize winner)** while talking to [Herbert Anderson](https://en.wikipedia.org/wiki/Herbert_L._Anderson):
  "You know, Herb, Johnny can do calculations in his head ten times as fast as I can! And I can do them ten times as fast as you can, Herb, so you can see how impressive Johnny is!"

- **[George Pólya](https://en.wikipedia.org/wiki/George_P%C3%B3lya) (mathematician, and whose lectures von Neumann attended as a student)**:
  "Johnny was the only student I was ever afraid of. If in the course of a lecture I stated an unsolved problem, the chances were he'd come to me at the end of the lecture with the complete solution scribbled on a slip of paper."

- **[Edward Teller](https://en.wikipedia.org/wiki/Edward_Teller) (father of the hydrogen bomb)**:
  "Von Neumann would carry on a conversation with my 3-year-old son, and the two of them would talk as equals, and I sometimes wondered if he used the same principle when he talked to the rest of us."

- **[Hans Bethe](https://en.wikipedia.org/wiki/Hans_Bethe) (Nobel Prize winner)**:
  "I have sometimes wondered whether a brain like von Neumann's does not indicate a species superior to that of man."

- **[Stanislaw Ulam](https://en.wikipedia.org/wiki/Stanislaw_Ulam) (co-inventor of the Monte Carlo method)**:
  "I have had a brain, and von Neumann had a computer."

- **[Claude Shannon](https://en.wikipedia.org/wiki/Claude_Shannon) (father of information theory)**:
  "the smartest person I've ever met."
- **[Marina von Neumann Whitman](https://en.wikipedia.org/wiki/Marina_von_Neumann_Whitman) (his daughter)**:
  "Although he genuinely adored my mother, my father's first love in life was thinking, a pursuit that occupied most of his waking hours."

![Von Neumann and Oppenheimer together in-front of one of the computing machines used on the hydrogen bomb project. Von Neumann could do calculations in his head faster than these early computers and would sometimes face off against them in competitions meant to entertain the other people in the labs](von_neumann_oppenheimer.jpeg)

If you want to know more about von Neumann, I recommend his biography:
[The Man from the Future: The Visionary Life of John von Neumann](https://www.goodreads.com/book/show/61089520-the-man-from-the-future)
by Ananyo Bhattacharya.

## The Fly Puzzle

One of the most famous stories about von Neumann is the fly puzzle.
This was reported by [Eugene Wigner](https://en.wikipedia.org/wiki/Eugene_Wigner)
in the 1966 documentary on Von Neumann.
Below is the exact part where Wigner tells the story:

{{ youtube(id="HpJgBcE-cFQ?start=184") }}

The tale takes place in Los Alamos during the Manhattan Project.
[Max Born (Nobel Prize winner)](https://en.wikipedia.org/wiki/Max_Born)
told von Neumann's the following puzzle:

> Two bicycles begin 20 miles apart,
> and each travels toward the other at 10 miles per hour until they collide;
> meanwhile, a fly travels continuously back and forth between the bicycles
> at 15 miles per hour until it is squashed in the collision.
> How far does the fly travel in total?

One can solve this rather easily by not paying attention to the inherent infinite geometric series that the fly travels.
Instead, focus on the fact that the fly is squashed when the bicycles collide,
and that the two bicycles will collide in one hour.
Thus, the fly travels 15 miles in total.

By the time Born had finished the question, von Neumann had already solved it.
He said "Why? 15 miles, of course."
Born was surprise and said that Johnny was "one of my first scientist friends that saw the solution immediately."
Johnny then replied "I can't understand that. It is a simple infinite geometrical series."

Now, to understand how fast von Neumann's mind was, let's solve the problem the way he did.
Note that the fly reaches the second bicycle when

$$ 15t = 20 - 10t,$$

where $t$ is the time in hours.
Note that $t_1$ is

$$ t_1 = \frac{20}{25} = \frac{4}{5}.$$

This means that the total time it takes for the fly to reach the second bicycle for the first time
is $\frac{4}{5}$ hours and the total distance traveled by the fly is
$d_1 = 15 \times \frac{4}{5} = 12$ miles.
It then turns around and reaches the first bicycle when

$$ 12 - 15t = 8 + 10t.$$

Solving for $t_2$ we get

$$ t_2 = \frac{4}{25}.$$

Continuing, the total distance traveled by the fly is given by summing the series

$$ 15 \sum\_{n=1}^{\infty} \frac{4}{5^n} = 15.$$

This is a classical [geometric series](https://en.wikipedia.org/wiki/Geometric_series).
In general, a geometric series is written as $a + ar + ar^{2} + ar^{3} + \ldots$,
where a $a$ is the coefficient of each term and $r$ is the common ratio between adjacent terms.

Here we have $a = 12$ and $r = \frac{4}{5}$,
and we know it converges to $\frac{a}{1-r} = 15$ when $r < 1$.

That's how von Neumann solved the problem in his head in a matter of seconds.
