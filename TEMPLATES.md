# Writing Slang templates

A guide for agents and people who write `.slang` templates in an iyi
project. Slang looks like Slim, and most of what you know about Slim holds;
this page lists where Slang differs, and the mistakes that are easy to make.
The full syntax table is in the [README](README.md#syntax).

## Rendering

```iyi
import github.com/domify/slang::{Slang}

def page(title : String, items : Array(String)) : String
  Slang.render("views/page.slang")
end
```

- The template becomes iyi code at compile time. A mistake in it is a
  compile error that names the template's line, not a run-time error.
- The path is relative to the `.iyi` file that calls `Slang.render`.
- The template sees the local variables and arguments of that method, and
  the constants and functions the file can reach. Pass what it needs as
  arguments; there is no context object.
- For a layout, render the page first and pass it in as a `String`:
  `content = Slang.render("views/page.slang")`, then `main!= content` in
  the layout.

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
  work. Longer code goes in an `iyi:` block or, better, in a function of
  the `.iyi` file.

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
