// Generic page wrapper:
//   typst compile lib/page.typ --input path=/pages/X.md \
//     --input body=/.cache/bodies/X.typ
#import "/lib/template.typ": *

#let fm = parse-frontmatter(read(sys.inputs.path))
#let description = fm.at("description", default: none)
#let page-slug = sys.inputs.path.split("/").last().replace(regex("\\.md$"), "")
#let active-nav = if page-slug in ("about", "contact") { page-slug } else { none }

#show: setup
#set document(title: site-title + " - " + fm.title, description: description)

#chrome(active: active-nav, {
  html.elem("h1", fm.title)
  render-body(sys.inputs.body)
})
