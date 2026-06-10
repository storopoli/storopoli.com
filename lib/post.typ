// Generic post wrapper: typst compile lib/post.typ --input path=/posts/X.md
#import "/lib/template.typ": *

#let src = read(sys.inputs.path)
#let parts = src.split("---\n")
#let fm = yaml(bytes(parts.at(1)))
#let body-src = parts.slice(2).join("---\n")

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
    html.elem(
      "section",
      attrs: (class: "header"),
      "Posted on " + display-date(iso) + " by " + author,
    )
    if tags.len() > 0 {
      html.elem("div", attrs: (class: "info"), {
        "Tags: "
        tags.map(t => html.elem("a", attrs: (href: "/tags/" + slugify(t) + ".html"), t)).join(", ")
      })
    }
    if show-toc {
      html.elem("div", attrs: (id: "table-of-contents", class: "toc"), {
        html.elem("p", attrs: (class: "toc-title"), "Contents")
        outline(title: none, depth: toc-depth)
      })
    }
    html.elem("section", render-md(body-src))
    if fm.at("bib", default: false) {
      bibliography("/bib/bibliography.bib", style: "/bib/style.csl")
    }
  })
})
