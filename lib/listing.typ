// Listing pages (index, archive, per-tag), driven by .cache/posts.json:
//   typst compile lib/listing.typ --input kind=index
//   typst compile lib/listing.typ --input kind=archive
//   typst compile lib/listing.typ --input kind=tag --input tag=math
#import "/lib/template.typ": *

#let posts = json("/.cache/posts.json")
#let kind = sys.inputs.kind
#let tag = sys.inputs.at("tag", default: none)

#let shown = if kind == "index" {
  posts.slice(0, calc.min(10, posts.len()))
} else if kind == "tag" {
  posts.filter(p => p.tags.contains(tag))
} else {
  posts
}

#let title = if kind == "index" {
  "Home"
} else if kind == "tag" {
  "Posts tagged \"" + tag + "\""
} else {
  "Archives"
}

#let post-list-of(items) = html.elem("ul", attrs: (class: "post-list"), for p in items {
  html.elem("li", {
    html.elem("time", attrs: (class: "post-date", datetime: date-iso(p.date)), date-iso(p.date))
    html.elem("a", attrs: (href: p.url, class: "post-link"), p.title)
  })
})

#let post-list = post-list-of(shown)

#let all-tags = posts.map(p => p.tags).flatten().dedup().sorted()

#show: setup
#set document(title: site-title + " - " + title)

#chrome({
  if kind == "index" {
    // No visible "Home" heading; the welcome line leads the page.
    html.elem("p", "Welcome to my blog!")
    html.elem("p", "I've reproduced a list of recent posts here for your reading pleasure:")
    html.elem("h2", attrs: (class: "section-label"), "Posts")
    post-list
    html.elem("p", {
      "…or you can find more in the "
      html.elem("a", attrs: (href: "/archive.html"), "archives")
      "."
    })
  } else if kind == "tag" {
    html.elem("h1", attrs: (class: "tag-title"), tag)
    html.elem("p", "Here are all posts tagged with this category:")
    post-list
  } else {
    html.elem("h1", title)
    html.elem("p", "Here you can find all my previous posts:")
    post-list
    html.elem("h2", attrs: (class: "section-label"), "By tag")
    for t in all-tags {
      html.elem("h3", attrs: (class: "tag-heading"), html.elem("a", attrs: (
        href: "/tags/" + slugify(t) + ".html",
        class: "tag",
      ), t))
      post-list-of(posts.filter(p => p.tags.contains(t)))
    }
  }
})
