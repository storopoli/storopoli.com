---
title: Zig comptime is such a powerful built-in feature
date: 2024-11-03
author: Jose Storopoli
description: A deep dive into the `comptime` feature of the Zig programming language.
tags: [zig, compiler, rust, programming]
---

I have been following the development of [Zig](https://ziglang.org/)
for a while now.
I like the idea of a systems programming language
that is **simple to learn and use,
_yet_ powerful and expressive**.

With Rust, I can get the powerful and expressive part,
_but_ the **learning curve is a bit steep**,
and some parts of the language are **complex
and hard to understand**.
For example `async`/`await` (specially if you have to deal with `Stream`s and `Pin`s);
and the macro domain-specific language (DSL).

Now back to Zig.
The language can be learned in one lazy morning.
That's exactly what I did and then played around
[migrating some C code to Zig from an old course](https://github.com/storopoli/graphs-complexity/pull/21)
that I used to teach about algorithmic complexity.
The code is now simpler and more readable than the original C code.
I have hugely benefited from Zig's built-in features such as:

- [**Optionals**](https://ziglang.org/documentation/master/#Optionals)
- [**Error handling**](https://ziglang.org/documentation/master/#Errors)
- [**`comptime`** (more on that, since it is the main topic of this post)](https://ziglang.org/documentation/master/#comptime)
- [**safe integer/floating-point arithmetic**](https://ziglang.org/documentation/master/#Operators)
- [**deferring memory deallocation** to the end of the scope](https://ziglang.org/documentation/master/#defer)
- [**`struct`s with functions** (methods)](https://ziglang.org/documentation/master/#struct)
- [**BYOA** (Bring Your Own Allocator)](https://ziglang.org/documentation/master/#Choosing-an-Allocator)[^BYOA]

[^BYOA]:
    {-} Zig doesn't have a built-in allocator.
    And I don't know it the acronym BYOA is a thing.
    I just made it up. But it makes sense, right?

Writing in Zig, comparing to C, is such a joy and you are always sure that
you won't spend hours debugging because Zig has:

- **No hidden control flow**
- **No hidden memory allocations**
- **No preprocessor, no macros**

I highly recommend you to give Zig a try.
It is the **ultimate C killer**.
In fact, you can **compile and interop C and Zig** code with Zig.
So you can start migrating your C codebase to Zig incrementally.
As an additional caveat, **Zig can be faster than C**.

## Zig's `comptime`

I've been wanting to write about Zig for a while now.
But I had no topic in mind.
Then, I was inspired by this talk by [matklad](https://matklad.github.io)
on modern systems programming comparing
Rust and Zig interwoven with his
professional journey from Rust to Zig,
and the amazing work he's doing at
[TigerBeetle](https://tigerbeetle.com):

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
    src="https://www.youtube.com/embed/4aLy6qjhHeo?t=1904"
    frameborder="0"
    allowfullscreen
  ></iframe>
</div>

The talk goes on to compare Rust and Zig in terms of systems programming.
Then, at the middle of the talk, he starts to talk about Zig.
One of the Zig's features that he covers is Zig's `comptime` feature
which allows to **run code and evaluate expressions at compile-time**
_without_ the need for meta-programming/macros or code generation.

Let me explain now what is `comptime` in Zig.
You can do `comptime` in Zig in different places, such as:

1. **Parameters of functions**
1. **Variables**
1. **Expressions**

Here are some examples thanks to [Loris Cro](https://kristoff.it/blog/what-is-zig-comptime/)
and [Zig's documentation](https://ziglang.org/documentation/master/#comptime).

### Parameters of functions

The first Zig code example is about using `comptime`
to decide the length of a statically-allocated array:

```zig
fn multiply(a: i64, b: i64) i64 {
    return a * b;
}

pub fn main() void {
    const len = comptime multiply(4, 5);
    const my_static_array: [len]u8 = undefined;
}
```

### Variables

The second example is about using `comptime` to define a variable.
This Zig code evaluates a Fibonacci number at compile-time:

```zig
const expect = @import("std").testing.expect;

fn fibonacci(index: u32) u32 {
    if (index < 2) return index;
    return fibonacci(index - 1) + fibonacci(index - 2);
}

test "fibonacci" {
    // test fibonacci at run-time
    try expect(fibonacci(7) == 13);

    // test fibonacci at compile-time
    try comptime expect(fibonacci(7) == 13);
}
```

### Expressions

The final example is about using `comptime` to evaluate an expression.
The following Zig code evaluates a `for`-loop at compile-time.

```zig
const max = 10;
comptime var total = 0;
comptime {
    for (1..max) |i| {
        total += i;
    }
}
```

### Bonus example: Zig's Generics

Now you can see how impressive `comptime` is.
In fact, Zig's generics are implemented using `comptime`.
Check the Zig code below that creates a generic `List` data structure:

```zig
fn List(comptime T: type) type {
    return struct {
        items: []T,
        len: usize,
    };
}

// The generic List data structure can be instantiated by passing in a type:
var buffer: [10]i32 = undefined;
var list = List(i32){
    .items = &buffer,
    .len = 0,
};
```

### The caveats of `comptime`

`comptime` has some caveats.
`comptime` expressions must be known at compile-time.
That means:

1. At the callsite, the value must be known at compile-time, or it is a compile error.
1. In the function definition, the value is known at compile-time.

If you guarantee that the value is known at compile-time,
you can use `comptime` to evaluate anything at compile-time.

## The motivating example

The motivating example for this blog post is an explanation
that matklad gives in his talk about how they use `comptime` at TigerBeetle
to make sure that a `struct` that represents a header has no padding in its fields.

![TigerBeetle's header struct](/images/zig-header_padding.png)

Then, he said that to have the same checks at compile-time in Rust,
you would need to bring a lot of complexity with `proc-macro`s.
That made me curious about how hard it would be to do the same in Rust.

So here's a toy problem that I came up with to compare Zig and Rust.
Instead of checking for padding in fields of a `struct`,
I decided to simplify and check for zero-padding in a string.

### Zero padding check in Zig

In Zig, strings are arrays of bytes,
and you can iterate over them at compile-time:

```zig
const std = @import("std");

fn checkZeroPadding(comptime s: []const u8) void {
    for (s) |c| {
        if (c == '0') {
            @compileError("String contains zero-padding");
        }
    }
}

pub fn main() void {
    comptime {
        const str1 = "12345";
        const str2 = "01234";

        checkZeroPadding(str1); // This will compile
        checkZeroPadding(str2); // This will cause a compile-time error
    }
}
```

The code above uses `comptime` to check if a string has zero-padding.

### Zero padding check in Rust

Compare this to how to do the same thing in Rust.
We need to use a procedural macro to achieve the same result.
Note that [macros in Rust](https://doc.rust-lang.org/reference/macros.html)
have their own domain-specific language (DSL) that is not Rust itself.
Hence, you need to learn a new language to write a macro in Rust.

First create a library crate named `zero-padding-checker`
that exports a [`proc-macro`](https://doc.rust-lang.org/reference/procedural-macros.html)
and add a procedural macro to check for zero-padding in a string:

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, LitStr};

#[proc_macro]
pub fn check_zero_padding(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as LitStr);
    let value = input.value();

    if value.starts_with('0') {
        return quote! {
            compile_error!("String contains zero-padding");
        }
        .into();
    }

    quote! {
        #input
    }
    .into()
}
```

Then you call the macro in your code:

```rust
use zero_padding_checker::check_zero_padding;

fn main() {
    check_zero_padding!("12345"); // This will compile
    check_zero_padding!("01234"); // This will cause a compile-time error
}
```

The Rust code above is far more complex than the Zig code.
First, it requires dependency on `syn` and `quote` crates
(note that the `proc-macro` crate is provided by Rust's compiler).
Second, despite the fact that this is a simple example,
procedural macros in Rust have their own domain-specific language (DSL)
and the complexity can grow quickly as the problem becomes more complex.

## Conclusion

Yeah, **Zig is a great language and has a bright future ahead**.
**`comptime`** is a powerful feature that allows you to **run almost _any_ code at compile-time**.
It is built into the language and you don't need to learn a new language to use it
or bring external dependencies to make it work.

If you like to **learn more about Zig**, I recommend reading the
[learn section of Zig's documentation](https://ziglang.org/learn/).
Also, to learn more about **Zig's `comptime`** feature,
check [Zig's documentation on `comptime`](https://ziglang.org/documentation/master/#comptime).
