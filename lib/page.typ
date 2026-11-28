// Generic page wrapper:
//   typst compile lib/page.typ --input path=/pages/X.md \
//     --input body=/.cache/bodies/X.typ
#import "/lib/template.typ": *

#let fm = parse-frontmatter(read(sys.inputs.path))
#let description = fm.at("description", default: none)

#show: setup
#set document(title: site-title + " - " + fm.title, description: description)

#chrome({
  html.elem("h1", fm.title)
  render-body(sys.inputs.body)
})
