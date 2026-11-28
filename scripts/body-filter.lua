--[[
Pandoc Lua filter: markdown -> typst body for storopoli.com.

- Raw formats: reject anything other than allowed HTML first (before later
  passes emit RawBlock/RawInline('typst', ...)). In particular, Pandoc raw
  Typst blocks/inlines would otherwise survive conversion and be eval()ed
  by the templates, bypassing the raw-HTML allowlist.
- Images & linked images: pandoc would emit #figure(image(..)) (and typst
  HTML export embeds image() files as base64 data URIs), and linked images
  ([![cap](img)](href)) would nest <figure> inside <a> inside <p>. Emit
  the template's md-img helper (real <img>, optional <a>, and <figcaption>
  with preserved Typst math) and unwrap standalone containers into blocks.
- Math: posts contain TYPST math syntax inside $...$, not LaTeX. Pandoc
  stores the math string verbatim in the AST, so emit it back untouched
  instead of letting the typst writer run it through texmath.
]]

local function typst_str(s)
  return '"' .. s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n'):gsub('\r', '\\r') .. '"'
end

local function convert_math(el)
  if el.mathtype == 'InlineMath' then
    return pandoc.RawInline('typst', '$' .. el.text .. '$')
  end
  return pandoc.RawInline('typst', '$ ' .. el.text .. ' $')
end

local caption_writer_opts = pandoc.WriterOptions({ wrap_text = 'wrap-none' })

-- Render caption Inlines to Typst markup while preserving Typst math
-- ($...$) verbatim instead of letting the typst writer run texmath.
local function caption_to_typst(inlines)
  if #inlines == 0 then
    return ''
  end
  local doc = pandoc.Pandoc({ pandoc.Plain(inlines) }):walk({
    Math = convert_math,
  })
  local rendered = pandoc.write(doc, 'typst', caption_writer_opts)
  return (rendered:gsub('\n+$', ''))
end

local function emit_md_img(img, href)
  local alt = pandoc.utils.stringify(img.caption):gsub('[\r\n]+', ' ')
  local caption = caption_to_typst(img.caption)
  local parts = {
    typst_str(img.src),
    'alt: ' .. typst_str(alt),
  }
  if caption:match('%S') then
    table.insert(parts, 'caption: [' .. caption .. ']')
  end
  if href ~= nil and href ~= '' then
    table.insert(parts, 'href: ' .. typst_str(href))
  end
  return '#md-img(' .. table.concat(parts, ', ') .. ')'
end

local function is_md_img_raw(el, tag)
  return el.t == tag and el.format == 'typst' and el.text:sub(1, 8) == '#md-img('
end

local function html_to_typst(html)
  -- YouTube embed iframe; the youtube() helper emits the hardened
  -- youtube-nocookie wrapper whatever the source host was. The capture
  -- keeps any query string (e.g. ?start=184) and normalizes t= to start=
  -- because YouTube /embed/ URLs ignore t=.
  local id = html:match(
    '<iframe[^>]*src="https://www%.youtube[%w%-%.]*%.com/embed/([^"]+)"')
  if id then
    id = id:gsub('&amp;', '&')
           :gsub('([?&])t=(%d+)s?([&#])', '%1start=%2%3')
           :gsub('([?&])t=(%d+)s?$', '%1start=%2')
    return '#youtube(' .. typst_str(id) .. ')'
  end
  -- embed wrapper tags around the iframe (the helper recreates the div)
  if html:match('^<div class="embed%-container">$')
    or html:match('^</div>$')
    or html:match('^</iframe>$') then
    return ''
  end
  -- standalone <img>: keep src/alt/class (about page profile picture)
  if html:match('^<img%s') then
    local src = html:match('src="([^"]+)"') or ''
    local alt = html:match('alt="([^"]*)"') or ''
    local class = html:match('class="([^"]*)"') or ''
    return '#raw-img(' .. typst_str(src) .. ', alt: ' .. typst_str(alt)
      .. ', class: ' .. typst_str(class) .. ')'
  end
  if html:match('^<br%s*/?>$') then
    return '#linebreak()'
  end
  -- harmless comments
  if html:match('^<!%-%-') then
    return ''
  end
  return nil
end

local function reject_raw(el, kind)
  io.stderr:write('body-filter.lua: unhandled raw ' .. kind .. ' format '
    .. el.format .. ': ' .. el.text:sub(1, 120) .. '\n')
  os.exit(1)
end

local function handle_raw_block(el)
  if el.format ~= 'html' then
    reject_raw(el, 'block')
  end
  local typst = html_to_typst(el.text)
  if typst == nil then
    io.stderr:write('body-filter.lua: unhandled raw HTML block: '
      .. el.text:sub(1, 120) .. '\n')
    os.exit(1)
  end
  return pandoc.RawBlock('typst', typst)
end

local function handle_raw_inline(el)
  if el.format ~= 'html' then
    reject_raw(el, 'inline')
  end
  local typst = html_to_typst(el.text)
  if typst == nil then
    io.stderr:write('body-filter.lua: unhandled raw inline HTML: '
      .. el.text:sub(1, 120) .. '\n')
    os.exit(1)
  end
  return pandoc.RawInline('typst', typst)
end

local function handle_linked_image(el)
  if #el.content == 1 and el.content[1].t == 'Image' then
    return pandoc.RawInline('typst', emit_md_img(el.content[1], el.target))
  end
  return nil
end

local function handle_image(el)
  return pandoc.RawInline('typst', emit_md_img(el, nil))
end

local function unwrap_md_img_block(el)
  if #el.content == 1 and is_md_img_raw(el.content[1], 'RawInline') then
    return pandoc.RawBlock('typst', el.content[1].text)
  end
  return nil
end

-- Pandoc wraps a standalone image in a Figure, which the typst writer
-- renders as #figure(..) around the #md-img(..) already produced —
-- duplicating the caption (plus a "Figure N:" prefix) in the HTML output.
-- Unwrap it: md-img owns the <figure>/<figcaption>.
local function unwrap_figure(el)
  if #el.content ~= 1 then
    return nil
  end
  local blk = el.content[1]
  if is_md_img_raw(blk, 'RawBlock') then
    return blk
  end
  if (blk.t == 'Plain' or blk.t == 'Para') and #blk.content == 1
    and is_md_img_raw(blk.content[1], 'RawInline') then
    return pandoc.RawBlock('typst', blk.content[1].text)
  end
  return nil
end

-- Run as explicit ordered passes:
-- 1. Validate/convert raw HTML & reject any raw Typst before later passes
--    emit RawBlock/RawInline('typst', ...).
-- 2. Convert linked images (Link wrapping a single Image) before Image or
--    Math run, so img.caption still holds raw Math AST nodes.
-- 3. Convert remaining Image nodes before Math runs, for the same reason.
-- 4. Convert remaining Math nodes and unwrap Figure/Para/Plain containers
--    around standalone #md-img(...) calls into top-level blocks.
return {
  {
    RawBlock = handle_raw_block,
    RawInline = handle_raw_inline,
  },
  {
    Link = handle_linked_image,
  },
  {
    Image = handle_image,
  },
  {
    Math = convert_math,
    Para = unwrap_md_img_block,
    Plain = unwrap_md_img_block,
    Figure = unwrap_figure,
  },
}
