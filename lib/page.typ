// Generic page wrapper:
//   typst compile lib/page.typ --input path=/pages/X.md \
//     --input body=/.cache/bodies/X.typ
#import "/lib/template.typ": *

#let src = read(sys.inputs.path)
#let parts = src.split("---\n")
#let fm = yaml(bytes(parts.at(1)))

#show: setup
#set document(title: site-title + " - " + fm.title)

#chrome({
  html.elem("h1", fm.title)
  render-body(sys.inputs.body)
})
