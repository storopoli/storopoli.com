--[[
Pandoc Lua filter: markdown -> typst body for storopoli.com.

- Math: posts contain TYPST math syntax inside $...$, not LaTeX. Pandoc
  stores the math string verbatim in the AST, so emit it back untouched
  instead of letting the typst writer run it through texmath.
- Images: pandoc would emit #figure(image(..)), and typst HTML export
  embeds image() files as base64 data URIs. Emit the template's md-img
  helper (real <img> + <figcaption>) instead.
- Raw HTML: typst has no raw-HTML primitive, so the known patterns are
  mapped to template helpers; anything unrecognized fails the build
  loudly rather than disappearing.
]]

local function typst_str(s)
  return '"' .. s:gsub('\\', '\\\\'):gsub('"', '\\"') .. '"'
end

function Math(el)
  if el.mathtype == 'InlineMath' then
    return pandoc.RawInline('typst', '$' .. el.text .. '$')
  end
  return pandoc.RawInline('typst', '$ ' .. el.text .. ' $')
end

function Image(el)
  local alt = pandoc.utils.stringify(el.caption)
  return pandoc.RawInline(
    'typst',
    '#md-img(' .. typst_str(el.src) .. ', alt: ' .. typst_str(alt) .. ')'
  )
end

local function html_to_typst(html)
  -- YouTube embed iframe; the youtube() helper emits the hardened
  -- youtube-nocookie wrapper whatever the source host was. The capture
  -- keeps any query string (e.g. ?start=184).
  local id = html:match(
    '<iframe[^>]*src="https://www%.youtube[%w%-%.]*%.com/embed/([^"]+)"')
  if id then
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

function RawBlock(el)
  if el.format ~= 'html' then
    return nil
  end
  local typst = html_to_typst(el.text)
  if typst == nil then
    io.stderr:write('body-filter.lua: unhandled raw HTML block: '
      .. el.text:sub(1, 120) .. '\n')
    os.exit(1)
  end
  return pandoc.RawBlock('typst', typst)
end

function RawInline(el)
  if el.format ~= 'html' then
    return nil
  end
  local typst = html_to_typst(el.text)
  if typst == nil then
    io.stderr:write('body-filter.lua: unhandled raw inline HTML: '
      .. el.text:sub(1, 120) .. '\n')
    os.exit(1)
  end
  return pandoc.RawInline('typst', typst)
end
