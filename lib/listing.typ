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
  "Archive"
}

#let active-nav = if kind == "index" {
  "home"
} else if kind == "archive" {
  "archive"
} else {
  none
}

#let post-list-detailed(items) = html.elem(
  "ul",
  attrs: (class: "post-list detailed"),
  for p in items {
    let iso = date-iso(p.date)
    let desc = p.at("description", default: none)
    let rt = p.at("reading_time", default: none)
    let ptags = p.at("tags", default: ())
    html.elem("li", {
      html.elem("time", attrs: (class: "post-date", datetime: iso), iso)
      html.elem("div", attrs: (class: "post-entry"), {
        html.elem("a", attrs: (href: p.url, class: "post-link"), p.title)
        if desc != none and desc != "" {
          html.elem("p", attrs: (class: "post-desc"), desc)
        }
        if ptags.len() > 0 or rt != none {
          html.elem("div", attrs: (class: "post-entry-meta"), {
            for t in ptags {
              html.elem("a", attrs: (
                href: "/tags/" + slugify(t) + ".html",
                class: "tag",
              ), t)
            }
            if rt != none {
              html.elem("span", attrs: (class: "read-time"), {
                if ptags.len() > 0 { "· " }
                str(rt) + " min read"
              })
            }
          })
        }
      })
    })
  },
)

// Sort alphabetically first; array.sorted is stable, so sorting by -count
// orders tags by post count descending, then alphabetically on ties.
#let all-tags = posts.map(p => p.tags).flatten().dedup().sorted()
#let tag-entries = {
  let counts = all-tags.map(t => (name: t, count: posts.filter(p => p.tags.contains(t)).len()))
  counts.sorted(key: it => -it.count)
}

#let years = posts.map(p => date-iso(p.date).slice(0, 4)).dedup().sorted().rev()

#let description = if kind == "index" {
  "Personal website and blog of Jose Storopoli, PhD — cryptography, mathematics, security engineering, Rust, and distributed systems."
} else if kind == "tag" {
  "All posts tagged \"" + tag + "\" on Jose Storopoli's blog."
} else {
  "Complete archive of all posts by Jose Storopoli, PhD, organized chronologically and by tag."
}

#show: setup
#set document(title: site-title + " - " + title, description: description)

#chrome(active: active-nav, {
  if kind == "index" {
    // No visible "Home" heading; the welcoming intro leads the page.
    html.elem("div", attrs: (class: "home-intro"), {
      html.elem(
        "p",
        attrs: (class: "lede"),
        "Welcome! Essays and notes on mathematics, programming, cryptography, and whatever else catches my curiosity.",
      )
      html.elem("p", attrs: (class: "sub"), {
        html.elem("a", attrs: (href: "/about.html"), "about →")
        " · "
        html.elem("a", attrs: (href: "/archive.html"), "archive →")
        " · "
        html.elem("a", attrs: (href: "/contact.html"), "contact →")
      })
    })
    html.elem("h2", attrs: (class: "section-label"), "Recent posts")
    post-list-detailed(shown)
    html.elem("p", attrs: (class: "archive-more"), html.elem(
      "a",
      attrs: (href: "/archive.html"),
      "Browse all " + str(posts.len()) + " posts in the archive →",
    ))
  } else if kind == "tag" {
    let count-label = if shown.len() == 1 { "1 post" } else { str(shown.len()) + " posts" }
    html.elem("h1", attrs: (class: "tag-title"), tag)
    html.elem("p", attrs: (class: "tag-meta"), {
      count-label
      " · "
      html.elem("a", attrs: (href: "/archive.html"), "all tags & archive →")
    })
    post-list-detailed(shown)
  } else {
    html.elem("h1", title)
    if tag-entries.len() > 0 {
      html.elem("nav", attrs: (class: "tag-index", "aria-label": "Tags"), {
        for entry in tag-entries {
          html.elem("a", attrs: (href: "/tags/" + slugify(entry.name) + ".html"), {
            html.elem("span", attrs: (class: "hash"), "#")
            entry.name
            html.elem("span", attrs: (class: "cnt"), str(entry.count))
          })
        }
      })
    }
    for y in years {
      let year-posts = posts.filter(p => date-iso(p.date).slice(0, 4) == y)
      let count-label = if year-posts.len() == 1 {
        "1 post"
      } else {
        str(year-posts.len()) + " posts"
      }
      html.elem("section", attrs: (class: "year-group"), {
        html.elem("h2", attrs: (class: "year-heading"), {
          html.elem("span", y)
          html.elem("span", attrs: (class: "year-count"), count-label)
        })
        html.elem(
          "ul",
          attrs: (class: "post-list compact"),
          for p in year-posts {
            let iso = date-iso(p.date)
            let ptags = p.at("tags", default: ())
            let shown-tags = ptags.slice(0, calc.min(2, ptags.len()))
            html.elem("li", {
              html.elem("div", attrs: (class: "row-main"), {
                html.elem("time", attrs: (class: "post-date", datetime: iso), iso.slice(5))
                html.elem("a", attrs: (href: p.url, class: "post-link"), p.title)
              })
              if shown-tags.len() > 0 {
                html.elem("span", attrs: (class: "row-tags"), {
                  for t in shown-tags {
                    html.elem("a", attrs: (
                      href: "/tags/" + slugify(t) + ".html",
                      class: "tag",
                    ), t)
                  }
                })
              }
            })
          },
        )
      })
    }
  }
})
