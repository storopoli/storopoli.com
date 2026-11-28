// Generic post wrapper:
//   typst compile lib/post.typ --input path=/posts/X.md \
//     --input body=/.cache/bodies/X.typ --input slug=X
#import "/lib/template.typ": *

#let fm = parse-frontmatter(read(sys.inputs.path))

#let iso = date-iso(fm.date)
#let updated = fm.at("updated", default: none)
#let updated-iso = if updated != none { date-iso(updated) } else { none }
#let author = fm.at("author", default: "Jose Storopoli")
#let raw-tags = fm.at("tags", default: ())
#let tags = if raw-tags == none { () } else { raw-tags }
#let description = fm.at("description", default: none)
#let show-toc = not fm.at("no-toc", default: false)
#let toc-depth = fm.at("toc-depth", default: 3)

#let posts = json("/.cache/posts.json")
#let slug = sys.inputs.at(
  "slug",
  default: sys.inputs.path.split("/").last().replace(regex("\\.md$"), ""),
)
#let idx = posts.position(p => p.slug == slug)
#let post-entry = if idx != none { posts.at(idx) } else { none }
#let reading-time = if post-entry != none {
  post-entry.at("reading_time", default: none)
} else {
  none
}
#let prev-post = if idx != none and idx + 1 < posts.len() {
  posts.at(idx + 1)
} else {
  none
}
#let next-post = if idx != none and idx > 0 {
  posts.at(idx - 1)
} else {
  none
}

#show: setup
#set document(title: site-title + " - " + fm.title, description: description)

#chrome(is-post: true, {
  html.elem("article", {
    html.elem("h1", fm.title)
    html.elem("div", attrs: (class: "post-meta"), {
      html.elem("time", attrs: (datetime: iso), iso)
      if updated-iso != none and updated-iso != iso {
        html.elem("span", attrs: (class: "post-updated"), {
          "updated "
          html.elem("time", attrs: (datetime: updated-iso), updated-iso)
        })
      }
      if reading-time != none {
        html.elem("span", attrs: (class: "reading-time"), str(reading-time) + " min read")
      }
      html.elem("span", author)
      if tags.len() > 0 {
        html.elem(
          "span",
          attrs: (class: "post-tags"),
          tags.map(t => html.elem("a", attrs: (
            href: "/tags/" + slugify(t) + ".html",
            class: "tag",
          ), t)).join(),
        )
      }
    })
    if show-toc {
      html.elem("details", attrs: (id: "table-of-contents", class: "toc"), {
        html.elem("summary", "Contents")
        outline(title: none, depth: toc-depth)
      })
    }
    html.elem("section", render-body(sys.inputs.body))
    if fm.at("bib", default: false) {
      bibliography("/bib/bibliography.bib", style: "ieee")
    }
  })
  if prev-post != none or next-post != none {
    html.elem("nav", attrs: (class: "post-nav", "aria-label": "Post navigation"), {
      if prev-post != none {
        html.elem("div", attrs: (class: "post-nav-prev"), html.elem("a", attrs: (
          href: prev-post.url,
          rel: "prev",
        ), {
          html.elem("span", attrs: (class: "post-nav-label"), "← Previous")
          html.elem("span", attrs: (class: "post-nav-title"), prev-post.title)
        }))
      }
      if next-post != none {
        html.elem("div", attrs: (class: "post-nav-next"), html.elem("a", attrs: (
          href: next-post.url,
          rel: "next",
        ), {
          html.elem("span", attrs: (class: "post-nav-label"), "Next →")
          html.elem("span", attrs: (class: "post-nav-title"), next-post.title)
        }))
      }
    })
  }
})
