-- pandoc Lua filter: WRITING.md §4 Markdown -> DESIGN.md §11.1 Word layout.
--   # Title            -> document title (Title style)
--   first paragraph    -> metadata line (Metadata style)
--   ## 1. Section      -> Heading 1, ### 1.1 -> Heading 2
--   **Label** alone    -> run-in label (Label style)
--   ![..](png) + *Figure N. caption* -> figure at text width with that caption
--   tables             -> widths from content (cell styles are set by md2docx.py)
--   > **Lead:** text   -> callout (Block Text style, set in reference.docx)

local stringify = pandoc.utils.stringify
local TEXT_WIDTH_IN = 6.5

local function styled(blocks, style)
  return pandoc.Div(blocks, { ["custom-style"] = style })
end

-- Column widths proportional to text length, but never narrower than the column's longest word.
local CHAR_IN, PAD_IN = 0.078, 0.3
local function widths_for(tbl)
  local ncol = #tbl.colspecs
  local total, longest = {}, {}
  for c = 1, ncol do total[c] = 0; longest[c] = 0 end
  local function add_row(row)
    for c, cell in ipairs(row.cells) do
      if c <= ncol then
        local text = stringify(cell.contents)
        total[c] = total[c] + math.min(#text, 300)
        for word in text:gmatch("%S+") do longest[c] = math.max(longest[c], #word) end
      end
    end
  end
  for _, row in ipairs(tbl.head.rows) do add_row(row) end
  for _, body in ipairs(tbl.bodies) do for _, row in ipairs(body.body) do add_row(row) end end
  local w, minw, sum = {}, {}, 0
  for c = 1, ncol do sum = sum + math.max(total[c], 1) end
  for c = 1, ncol do
    w[c] = math.max(total[c], 1) / sum
    minw[c] = math.min((longest[c] * CHAR_IN + PAD_IN) / TEXT_WIDTH_IN, 0.45)
  end
  -- Raise narrow columns to their minimum and take the space from the others.
  for _ = 1, 5 do
    local fixed, free = 0, 0
    for c = 1, ncol do
      if w[c] <= minw[c] then w[c] = minw[c]; fixed = fixed + w[c] else free = free + w[c] end
    end
    if free <= 0 then break end
    local scale = (1 - fixed) / free
    for c = 1, ncol do if w[c] > minw[c] then w[c] = w[c] * scale end end
  end
  return w
end

local function caption_from(block)
  -- *Figure N. text* on its own line
  if block and block.t == "Para" and #block.content == 1 and block.content[1].t == "Emph" then
    local text = stringify(block.content[1])
    if text:match("^Figure %d+%.") then return block.content[1].content end
  end
  return nil
end

local function full_width(fig)
  return fig:walk({
    Image = function(img)
      img.attributes.width = TEXT_WIDTH_IN .. "in"
      img.attributes.height = nil
      return img
    end,
  })
end

function Pandoc(doc)
  local blocks = doc.blocks
  local out = pandoc.List()
  local i = 1

  -- Title and metadata line.
  if blocks[1] and blocks[1].t == "Header" and blocks[1].level == 1 then
    doc.meta.title = pandoc.MetaInlines(blocks[1].content)
    i = 2
    if blocks[2] and blocks[2].t == "Para" then
      out:insert(styled({ blocks[2] }, "Metadata"))
      i = 3
    end
  end

  while i <= #blocks do
    local b = blocks[i]
    if b.t == "Header" then
      b.level = math.max(b.level - 1, 1)
      out:insert(b)
    elseif b.t == "Figure" then
      local cap = caption_from(blocks[i + 1])
      local fig = full_width(b)
      if cap then
        fig.caption = { long = { pandoc.Plain(cap) } }
        i = i + 1
      end
      out:insert(fig)
    elseif b.t == "Para" and #b.content == 1 and b.content[1].t == "Strong" then
      out:insert(styled({ pandoc.Para(b.content[1].content) }, "Label"))
    else
      out:insert(b)
    end
    i = i + 1
  end

  doc.blocks = out
  return doc
end
