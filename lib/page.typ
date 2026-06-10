// Generic page wrapper: typst compile lib/page.typ --input path=/pages/X.md
#import "/lib/template.typ": *

#let src = read(sys.inputs.path)
#let parts = src.split("---\n")
#let fm = yaml(bytes(parts.at(1)))
#let body-src = parts.slice(2).join("---\n")

#show: setup
#set document(title: site-title + " - " + fm.title)

#chrome({
  html.elem("h1", fm.title)
  render-md(body-src)
})
