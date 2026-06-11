// Generic post wrapper:
//   typst compile lib/post.typ --input path=/posts/X.md \
//     --input body=/.cache/bodies/X.typ
#import "/lib/template.typ": *

#let src = read(sys.inputs.path)
#let parts = src.split("---\n")
#let fm = yaml(bytes(parts.at(1)))

#let iso = date-iso(fm.date)
#let author = fm.at("author", default: "Jose Storopoli")
#let tags = fm.at("tags", default: ())
#let description = fm.at("description", default: none)
#let show-toc = not fm.at("no-toc", default: false)
#let toc-depth = fm.at("toc-depth", default: 3)

#show: setup
#set document(title: site-title + " - " + fm.title, description: description)

#metadata((
  title: fm.title,
  date: iso,
  description: description,
  tags: tags,
  author: author,
)) <frontmatter>

#chrome(is-post: true, {
  html.elem("h1", fm.title)
  html.elem("article", {
    html.elem("div", attrs: (class: "post-meta"), {
      html.elem("time", attrs: (datetime: iso), iso)
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
})
