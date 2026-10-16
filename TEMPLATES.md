# Writing Slang templates

A guide for agents and people who write `.slang` templates in a ris
project. Slang looks like Slim, and most of what you know about Slim holds;
this page lists where Slang differs, and the mistakes that are easy to make.
The full syntax table is in the [README](README.md#syntax).

## Rendering

```ruby
import github.com/domify/ris-slang::{Slang}

def page(title : String, items : Array(String)) : TapeString
  Slang.render("views/page.slang")
end

Tape.scope do
  html = page("Hello", ["one", "two"])
  # Consume html's bytes before this scope ends.
end
```

- `render(filename, capacity = 256)` returns a `TapeString` and requires the
  caller's active `Tape.scope`.
- `render_string(filename, capacity = 256)` returns an independent `String`.
  It renders on an independent `Tape.local`, copies before returning, and
  immediately releases its temporary buffers for reuse.
- `Tape.scope` shares an existing tape; `Tape.local` always owns a separate
  tape. A `render_string` template can read outer `TapeString` values; convert
  other outer tape values to owned data before entering the local tape.
- `Slang.embed` accepts a `Slang::TapeBuffer` or another writer with `<<`.
  A tape buffer's `finish` borrows its bytes; do not append after finishing.
- The template becomes ris code at compile time; diagnostics name the
  template's line. The path is relative to the calling `.ri` source file.
- Keep borrowed return types explicit (`: TapeString`). Use `.to_s` inside
  the scope when handing text to a retained destination requiring String.
- Templates see the caller's local variables, arguments and accessible
  constants/functions.
- For layouts, pass a rendered `TapeString` to another template within the
  same scope, or use `render_string` if it must outlive the scope. `!=`
  writes either result without escaping.
- Escaped/raw output and ordinary attributes accept `TapeString` directly.
  Classes retain their String/blank-filtering semantics. Helpers accepting
  nested HTML still receive a `String`, built with a heap builder.

## Output and escaping

| Write | For |
|---|---|
| `p= expr` | Escaped output. The default; use it for every value. |
| `p!= expr` | Raw output, for HTML you built and trust. |
| `p Hello, #{name}` | Text. The text is HTML, `#{}` in it is escaped. |
| `a href="/x/#{id}"` | An attribute. Its value is always escaped. |

- Raw output is `!=`, as in Haml. **`==` is an error**, unlike Slim and
  Crystal Slang.
- Use `!=` only for HTML your own code made; never for user input, unless
  every value in it went through `Slang.escape` or `HTML.escape`.
- Output on its own line is `= expr` or `!= expr`.

## Code

```slim
- visible = items.reject(&.blank?)
- if visible.empty?
  p Nothing yet.
- else
  ul
    - visible.each do |item|
      li= item
```

- `-` lines are **iyi**, not Ruby or Crystal: no `begin`/`rescue` (iyi
  has no exceptions), no `content_for`, no Kilt.
- Indentation closes blocks; never write `end`.
- `if`/`elsif`/`else`, `case`/`when`/`in`, `each do |x|` and assignments
  work. Longer code goes in an `ris:` block or, better, in a function of
  the `.ri` file.

## Attributes

```slim
a.button#buy href=url target="_blank" Buy
input type="checkbox" checked=selected
li class=(item == current ? "current" : nil) = item
```

- `true` writes the bare name (`checked`), `false` and `nil` leave the
  attribute out. Use that instead of an `if` around the tag.
- A value without quotes **ends at the first space** outside parentheses or
  brackets. Put a longer expression in parentheses, or compute it on a
  `- name = …` line first.
- After an unquoted value, output needs a space before its `=`:
  `li class=css = item`. After a tag or a quoted value it needs none:
  `p= name`, `a href="/"= name`.
- `.a.b class=x` joins the class names; blank names are left out, and an
  element without any has no `class` attribute.
- `tag *hash` writes each entry of a hash as an attribute.

## Whitespace

There is no whitespace between tags, as in Slim. `p` then `a` on the next
line renders as `<p>…</p><a>…</a>`. Where a space matters:

- `' text` is text followed by a space;
- `a<`, `a>`, `a<>` put a space before, after or around the element;
- `=<`, `=>` do the same for output.

## Checklist

- [ ] Every value is printed with `=`; `!=` only for trusted HTML.
- [ ] No `==` for output, and no `end` lines.
- [ ] No unquoted attribute value with a space outside parentheses.
- [ ] Spaces between inline elements and text, with `'`, `<` or `>`.
- [ ] The project builds: template errors are compile errors.
