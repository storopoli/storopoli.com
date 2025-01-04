+++
title = "Word Embeddings"
date = "2023-11-19T22:49:51"
author = "Jose Storopoli, PhD"

[taxonomies]
tags = ["math", "machine learning", "julia"]

[extra]
katex = true
+++

{% admonition(type="warning", icon="warning", title="Evil JavaScript") %}
This post uses [KaTeX](https://katex.org/) to render mathematical expressions.

To see the rendered mathematical expressions, you'll need to enable JavaScript.
{% end %}

![Euclid of Alexandria](euclid.jpg)

I wish I could go back in time and tell my younger self
that you can make a machine understand human language with trigonometry.
That would definitely have made me more aware and interested in the
subject during my school years.
I would have looked at triangles, circles, sines, cosines, and tangents
in a whole different way.
Alas, better late than never.

In this post, we'll learn how to represent words using word embeddings,
and how to use basic trigonometry to play around with them.
Of course, we'll use [Julia](https://julialang.org).

## Word Embeddings

**[Word embeddings](https://en.wikipedia.org/wiki/Word_embedding) is a way to
represent words as a real-valued vector that encodes the meaning of the word
in such a way that words that are closer in the vector space are expected
to be similar in meaning**.

Ok, let's unwrap the above definition.
First, a **real-valued vector** is any vector which its elements belong to the real
numbers.
Generally we denote vectors with a bold lower-case letter,
and we denote its elements (also called components) using square brackets.
Hence, a vector $\bold{v}$ that has 3 elements, $1$, $2$, and $3$,
can be written as

$$\bold{v} = \begin{bmatrix} 1 \\\ 2 \\\ 3 \end{bmatrix}$$

Next, what "close" means for vectors?
We can use distance functions to get a measurable value.
The most famous and commonly used distance function is the **Euclidean distance**,
in honor of [Euclid](https://en.wikipedia.org/wiki/Euclid), the "father of geometry",
and the guy pictured in the image at the top of this post.
The Euclidean distance is defined in trigonometry for 2-D and 3-D spaces.
However, it can be generalized to any dimension $n > 1$ by using vectors.

Since every word is represented by an $n$-dimensional vector,
we can use distances to compute a metric that represent similarity between vectors.
And, more interesting, we can add and subtract words
(or any other linear combination of one or more words) to generate new words.

Before we jump to code and examples, a quick note about how word embeddings
are constructed.
They are trained like a regular machine learning algorithm,
where the cost function measures the difference between
some vector distance between the vectors and a "semantic distance".
The goal is to iteratively find good vector values that minimize the cost.
So, if a vector is close to another vector measured by a distance function,
but far apart measured by some semantic distance on the words that these
vectors represent, then the cost function will be higher.
The algorithm cannot change the semantic distance, it is treated as a fixed value.
However, it can change the vector elements' values so that the vector distance function
closely resembles the semantic distance function.
Lastly, generally the dimensionality of the vectors used in word embeddings
are high, $n > 50$, since it needs a proper amount of dimensions in order to
represent all the semantic information of words with vectors.

## Pre-Trained Word Embeddings

Generally we don't train our own word embeddings from scratch,
we use pre-trained ones.
Here is a list of some of the most popular ones:

- [Word2Vec](https://code.google.com/archive/p/word2vec/):
  One of the first public available word embeddings,
  made by Google in 2013.
  Only supports English.
- [GloVe](https://nlp.stanford.edu/projects/glove/):
  made by Stanford in 2014.
  Only supports English.
- [FastText](https://fasttext.cc/):
  From Facebook, released in 2016.
  Supports hundreds of languages.

## Julia Code

We will use the [`Embeddings.jl`](https://github.com/JuliaText/Embeddings.jl)
package to easily load word embeddings as vectors,
and the [`Distances.jl`](https://github.com/JuliaStats/Distances.jl)
package for the convenience of several distance functions.
This is a nice example of the Julia package ecosystem composability,
where one package can define types, another can define functions,
and another can define custom behavior of these functions on types that
are defined in other packages.

```julia
julia> using Embeddings

julia> using Distances
```

Let's load the [GloVe](https://nlp.stanford.edu/projects/glove/)
word embeddings.
First, let's check what we have in store to choose from
GloVe's English language embeddings:

```julia
julia> language_files(GloVe{:en})
20-element Vector{String}:
 "glove.6B/glove.6B.50d.txt"
 "glove.6B/glove.6B.100d.txt"
 "glove.6B/glove.6B.200d.txt"
 "glove.6B/glove.6B.300d.txt"
 "glove.42B.300d/glove.42B.300d.txt"
 "glove.840B.300d/glove.840B.300d.txt"
 "glove.twitter.27B/glove.twitter.27B.25d.txt"
 "glove.twitter.27B/glove.twitter.27B.50d.txt"
 "glove.twitter.27B/glove.twitter.27B.100d.txt"
 "glove.twitter.27B/glove.twitter.27B.200d.txt"
 "glove.6B/glove.6B.50d.txt"
 "glove.6B/glove.6B.100d.txt"
 "glove.6B/glove.6B.200d.txt"
 "glove.6B/glove.6B.300d.txt"
 "glove.42B.300d/glove.42B.300d.txt"
 "glove.840B.300d/glove.840B.300d.txt"
 "glove.twitter.27B/glove.twitter.27B.25d.txt"
 "glove.twitter.27B/glove.twitter.27B.50d.txt"
 "glove.twitter.27B/glove.twitter.27B.100d.txt"
 "glove.twitter.27B/glove.twitter.27B.200d.txt"
```

I'll use the `"glove.6B/glove.6B.50d.txt"`.
This means that it was trained with 6 billion tokens,
and it provides embeddings with 50-dimensional vectors.
The `load_embeddings` function takes an optional second positional
argument as an `Int` to choose from which index of the `language_files` to use.
Finally, I just want the words "king", "queen", "man", "woman";
so I am passing these words as a `Set` to the `keep_words` keyword argument:

```julia
julia> const glove = load_embeddings(GloVe{:en}, 1; keep_words=Set(["king", "queen", "man", "woman"]));
Embeddings.EmbeddingTable{Matrix{Float32}, Vector{String}}(Float32[-0.094386 0.50451 -0.18153 0.37854; 0.43007 0.68607 0.64827 1.8233; … ; 0.53135 -0.64426 0.48764 0.0092753; -0.11725 -0.51042 -0.10467 -0.60284], ["man", "king", "woman", "queen"])
```

Watch out with the order that we get back.
If you see the output of `load_embeddings`,
the order is `"man", "king", "woman", "queen"]`
Let's see how a word is represented:

```julia
julia> queen = glove.embeddings[:, 4]
50-element Vector{Float32}:
  0.37854
  1.8233
 -1.2648
  ⋮
 -2.2839
  0.0092753
 -0.60284
```

They are 50-dimensional vectors of `Float32`.

Now, here's the fun part:
let's add words and check the similarity between the
result and some other word.
A classical example is to start with the word "king",
subtract the word "men",
add the word "woman",
and check the distance of the result to the word "queen":

```julia
julia> man = glove.embeddings[:, 1];

julia> king = glove.embeddings[:, 2];

julia> woman = glove.embeddings[:, 3];

julia> cosine_dist(king - man + woman, queen)
0.13904202f0
```

This is less than 1/4 of the distance of "woman" to "king":

```julia
julia> cosine_dist(woman, king)
0.58866215f0
```

Feel free to play around with others words.
If you want suggestions, another classical example is:

```julia
cosine_dist(Madrid - Spain + France, Paris)
```

## Conclusion

I think that by allying interesting applications to abstract math topics
like trigonometry is the vital missing piece in STEM education.
I wish every new kid that is learning math could have the opportunity to contemplate
how new and exciting technologies have some amazing simple math under the hood.
If you liked this post, you would probably like [linear algebra](https://en.wikipedia.org/wiki/Linear_algebra).
I would highly recommend [Gilbert Strang's books](https://math.mit.edu/~gs/)
and [3blue1brown series on linear algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab).
