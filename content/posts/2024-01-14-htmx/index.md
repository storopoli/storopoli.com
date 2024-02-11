+++
title = "htmx: an Oasis in a Desert of Soy"
date = "2024-01-14T06:13:19-03:00"
tags = ["htmx", "javascript", "rust"]
categories = []
javascript = true
math = false
mermaid = true
+++

> Warning: This post has [`mermaid.js`](https://mermaid.js.org) enabled,
> so if you want to view the rendered diagrams,
> you'll have to unfortunately enable JavaScript.

![htmx bell curve](bellcurve.png#center)

I love to learn new things and I'm passionate about Stoic philosophy.
So, when I acquired the domain
[`stoicquotes.io`](https://stoicquotes.io)[^stoicquotes],
I've decided to give [`htmx`](https://htmx.org) a try.

[^stoicquotes]: you can find the source code at
[`storopoli/stoic-quotes`](https://github.com/storopoli/stoic-quotes).

## What is `htmx`?

**`htmx`** is a small JavaScript library that allows you to enhance your HTML with
attributes to perform AJAX (Asynchronous JavaScript and XML) without writing
JavaScript[^yavascript]. It focuses on extending HTML by adding custom attributes
that describe how to perform common dynamic web page behaviors like partial page
updates, form submission, etc. `htmx` is designed to be easy to use, requiring
minimal JavaScript knowledge, so that you can add interactivity[^htmx] to web pages
with just HTML.

[^yavascript]: YES, yes, no YavaScript. Hooray!
[^htmx]: `htmx` can do much more, such as lazy loading, infinite scroll,
or submitting forms without a full page reload, etc.

Let's contrast this with the [Soy stuff](../2023-11-10-2023-11-13-soydev/)
like the notorious React framework. **React**, on the other hand, is a JavaScript
library for building user interfaces, primarily through a component-based
architecture. It manages the creation of user interface elements, updates the UI
efficiently when data changes, and helps keep your UI in sync with the state of
your application. React requires a deeper knowledge of JavaScript and understanding
of its principles, such as components, state, and props.

**In simple terms:**

- **`htmx`** enhances plain HTML by letting you add attributes for dynamic
  behaviors, so you can make webpages interactive with no JavaScript coding;
  you can think of it as boosting your HTML to do more.
- **React** is more like building a complex machine from customizable parts that
  you program with JavaScript, giving you full control over how your application
  looks and behaves but also requiring more from you in terms of code complexity
  and architecture.

Additionally, React can be slower and less performant than `htmx`.
This is due to `htmx` manipulating the actual
[DOM](https://en.wikipedia.org/wiki/Document_Object_Model) itself,
while React updates objects in the Virtual DOM. Afterward, React compares the
new Virtual DOM with a pre-update version and calculates the
most efficient way to make these changes to the real DOM.
So React has to do this whole trip around diff'ing all the time the Virtual DOM
against the actual DOM for **every fucking change**.

Finally, `htmx` receives pure HTML from the server.
React needs to the **JSON busboy thing**: the server sends JSON, React parses
JSON into JavaScript code, then it parses it again to HTML for the browser.

Here are some [`mermaid.js`](https://mermaid.js.org/) diagrams to illustrate
what is going on under the hood:

{{<mermaid>}}

---

title: htmx
---

flowchart LR
HTML --> DOM
{{</mermaid>}}

{{<mermaid>}}

---

title: React
---

flowchart LR
JSON --> JavaScript --> HTML --> VDOM[Virtual DOM] --> DOM
{{</mermaid>}}

A consequence of these different paradigms is that `htmx` don't care about
what the server sends back and will happily include in the DOM.
Hence, front-end and back-end are decoupled and less complex.
Whereas in Reactland, we need to have a tight synchronicity between front-end
and back-end. If the JSON that the server sends doesn't conform to the exact
specifications of the front-end, the application ~~becomes a dumpster fire~~
breaks.

## Hypermedia

When the web was created it was based on the concept of
[**Hypermedia**](https://en.wikipedia.org/wiki/Hypermedia).
Hypermedia refers to a system of interconnected multimedia elements, which can
include text, graphics, audio, video, and hyperlinks. It allows users to
navigate between related pieces of content across the web or within
applications, creating a non-linear way of accessing information.

HTML follows the Hypermedia protocol. HTML is the native language of browsers[^wasm].
That's why all the React-like frameworks have to convert JavaScript into HTML.
So it's only natural to rely primarily on HTML to deliver content and sprinkle
JavaScript sparingly when you need something that HTML cannot offer.

[^wasm]: actually we also have [WASM](https://webassembly.org).

Unfortunately, HTML has stopped in time. Despite all the richness of
[HTTP](https://en.wikipedia.org/wiki/HTTP) with the diverse request methods:
`GET`, `HEAD`, `POST`, `PUT`, `DELETE`, `CONNECT`, `OPTIONS`, `TRACE`, `PATCH`;
HTML only has _two_ elements that interact with the server:

- `<a>`: sends a `GET` request to fetch new data.
- `<form>`: sends a `POST` request to create new data.

That's the main purpose of `htmx`: allowing HTML elements to leverage all the
capabilities of HTTP.

## `htmx` in Practice

OK, enough of abstract and theoretical concepts. Let's see how `htmx` works in
practice.

First, the only thing you need to do enable `htmx` is to insert this `<script>`
tag in your HTML:

```html
<script src="https://unpkg.com/htmx.org@{version}"></script>
```

where `{version}` is the desired `htmx` version that you'll want to use.
I has around 40kb of size.

Inside the code behind [`stoicquotes.io`](https://stoicquotes.io)[^stoicquotes],
we have the following HTML[^code]:

[^code]: I've simplified a bit removing some styling for the purpose of clarity.

```html
<div>
    <blockquote id="quote">
        Some nice Stoic quote...
    </blockquote>
</div>
<button hx-get="/quote" hx-trigger="click" hx-target="#quote" hx-swap="outerHTML">
    New
</button>
```

When the user clicks (`hx-trigger`) in the "New" button, `htmx` sends a `GET`
request to the `/quote` endpoint (`hx-get`). Then it swaps the whole HTML
(`hx-swap`) of the element that has id "quote" (`hx-target`).
This is accomplished without a single character of JavaScript.
Instead we extend HTML by adding new attributes to the HTML elements:

- `hx-get`
- `hx-trigger`
- `hx-target`
- `hx-swap`

The server replies with a new `<blockquote>` element every time it gets a `GET`
request in the `/quote` endpoint.

This is truly amazing. We just used one line of `htmx`.

![htmx 4 lines](4-lines.png#center)

`htmx` adheres to my trifecta of amazing tools[^trifecta]:

[^trifecta]: there are some other tools that I use that adhere to the trifecta.
Most notoriously is [Julia](https://julialang.org) and
[Rust](https://rust-lang.org).

- powerful
- expressive
- concise

Here's a breakdown of what the trifecta of amazing tools means:

1. **Powerful:**
   A powerful tool has the capability to handle complex, demanding tasks with
   relative ease. It possesses the strength, performance, and features necessary to
   accomplish a wide range of functions.

1. **Expressive:**
   An expressive tool gives users the ability to articulate complex ideas,
   designs, or concepts with simplicity and nuance. It provides a rich set of
   capabilities that allow for diverse and sophisticated forms of expression.

1. **Concise:**
   A concise tool allows for achieving goals with minimal effort or complexity.
   It focuses on efficiency and effectiveness, often through simplification and the
   removal of unnecessary components. It should be capable of performing tasks
   without requiring verbose instructions or processes.

### How we would do this in React?

Now compare this with React.

First, we need to install React.
This is not simple, but here's a breakdown:

1. install Node.js
1. install React: `npm install react react-dom`
1. create an `index.js` file with some variant of:

   ```javascript
   import { createRoot } from 'react-dom/client';

   document.body.innerHTML = '<div id="app"></div>';

   const root = createRoot(document.getElementById('app'));
   root.render(<h1>Hello, world</h1>);
   ```

And now here's the code for the `Quote` component:

```jsx
import React, { useState } from 'react';

const Quote = () => {
  const [quote, setQuote] = useState('Some nice Stoic quote...');

  const fetchNewQuote = async () => {
    try {
      const response = await fetch('/quote');
      const newQuote = await response.text();
      setQuote(newQuote);
    } catch (error) {
      console.error('Error fetching new quote:', error);
    }
  };

  return (
    <div>
      <blockquote id="quote">
        {quote}
      </blockquote>
      <button onClick={fetchNewQuote}>
        New
      </button>
    </div>
  );
}

export default Quote;
```

That's a LOT of JavaScript code.
The Soy Gods must be smiling upon you, my friend.

## Conclusion

I highly recommend that you check out [`htmx`](https://htmx.org),
especially the free [Hypermedia systems book](https://htmx.org/#book) which
goes into details and it is way more comprehensive than this short blog post.

`htmx` is a fresh and elegant approach to build simple reactive web pages.
It extends HTML to be able to use all of the capabilities of any JavaScript-based
reactive framework without a single drop of JavaScript.
You just add some new HTML attributes to your HTML elements.

I've had such joy using `htmx` lately.
It made me go back into my early teens, when I was doing HTML pages in
[GeoCities](https://en.wikipedia.org/wiki/GeoCities).
Good times, no JavaScript-bloated code.

## License

This post is licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
