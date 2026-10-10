# Slang

Lightweight, terse templates for [iyi](https://iyi.dev/), in the syntax of
[Slim](https://github.com/slim-template/slim).

Slang started in 2016 as a template language for Crystal. This repository
is its continuation as a native iyi module: the lexer, parser and code
generation of the last Crystal release (2.0.3) are ported to iyi, along with
its tests. The Crystal code is kept unchanged in
[`archive/crystal/`](archive/crystal/) and is no longer maintained. The iyi
port is maintained by Priit Tark at [domify](https://github.com/domify).

Like the original, a template is turned into iyi code at compile time, so a
rendered page is ordinary compiled code by the time the program runs.

## Installation

```sh
iyi get github.com/domify/slang
```

## Usage

```iyi
import github.com/domify/slang::{Slang}

def page(name : String, items : Array(String)) : String
  Slang.render("views/page.slang")
end
```

`Slang.render("file.slang")` is the rendered template as a `String`.
`Slang.embed("file.slang", io)` writes it to `io`, anything with `<<`, such as
a `String::Builder`. The path is read beside the file that calls the macro,
or as it is when absolute. Local variables of the method that renders a
template are visible in it.

## Syntax

```slim
doctype html
html lang="en"
  head
    meta charset="utf-8"
    title= title
    css:
      h1 {color: red;}
  body
    /! A visible comment
    / An invisible comment
    h1.title Hello, #{name}!
    p
      ' Text is <em>HTML</em>,
      | and #{name} in it is escaped.
    div!= "<hr>"
    ul#items
      - items.each do |item|
        li class=(item == current ? "current" : nil) = item
    input type="checkbox" checked=true
    input type="checkbox" checked=false
    a(href="/about" title="About") About
    span<> spaced
    javascript:
      console.log("8 * 3 =", 8 * 3);
```

With `title = "Slang"`, `name = "<world>"`, `items = ["one", "two"]` and
`current = "two"`, this renders as (one line, broken here for reading):

```html
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Slang</title>
<style>h1 {color: red;}</style></head><body><!--A visible comment-->
<h1 class="title">Hello, &lt;world&gt;!</h1>
<p>Text is <em>HTML</em>, and &lt;world&gt; in it is escaped.</p><div><hr></div>
<ul id="items"><li>one</li><li class="current">two</li></ul>
<input type="checkbox" checked><input type="checkbox">
<a href="/about" title="About">About</a> <span>spaced</span>
<script>console.log("8 * 3 =", 8 * 3);</script></body></html>
```

| Syntax | Meaning |
|---|---|
| `tag`, `.class`, `#id`, `tag.class#id` | An element; `.class` and `#id` alone are a `div`. |
| `tag attr="text #{expr}"`, `tag attr=expr` | Attributes. `true` writes the bare name, `false` and `nil` leave it out. Values are escaped. |
| `tag(…)`, `tag[…]`, `tag{…}` | Attributes inside brackets. |
| `tag *hash` | Every entry of a hash as an attribute; its `class` joins the others. |
| `tag: tag` | An element nested on the same line. |
| `tag text`, `\| text` | Text, which is HTML; `#{expr}` in it is escaped. |
| `' text` | Text followed by a space. |
| `tag= expr`, `tag!= expr`, `= expr`, `!= expr` | Output, escaped or raw, in the element or on its own line. `=<`, `=>`, `tag<` and `tag>` put a space before or after. |
| `= expr do \|x\|` | A method that takes the nested HTML as a block's `String`, such as a form helper. |
| `- code` | iyi code: `if`/`elsif`/`else`, `case`/`when`/`in`, `each do`, assignments. |
| `/ text`, `/! text`, `/[if IE]` | An invisible, a visible and a conditional comment. |
| `javascript:`, `css:` | A `script` or `style` element with verbatim text. |
| `iyi:`, `crystal:` | Lines of iyi code. |
| `doctype html` | `<!DOCTYPE html>`. |

As in Slim, there is no whitespace between tags. An attribute value without
quotes ends at the first space outside parentheses or brackets, so compute a
long expression in a `- name = …` line first. For the same reason, output
after such a value needs a space before its `=`, as in `li class=css = item`;
after a tag or a quoted value, `p= name` and `a href="/"= name` need none.

## Differences from Crystal Slang 2.0.3

- Raw output is `!=`, as in Haml and Pug, so it does not read as a
  comparison; `==` stops the template with an error.
- An attribute whose value is `false` or `nil` is left out and `true` writes
  the bare name, including `id` and the entries of a `*splat` hash.
- Blank class names are left out, and an element without a class name has no
  `class` attribute.
- `iyi:` opens a code block, as `crystal:` does.
- `begin`/`rescue` lines are parsed, but iyi has no exceptions, so they do not
  compile. Kilt and Kemal's `content_for` are not supported.
- Fixed bugs of the original:
  - `=<` and `=>` put a space before and after the output; the original
    added it to the code.
  - Comparisons such as `a == b` and `a != b` inside an attribute value are
    kept; the original dropped every `=` in it.
  - An attribute value such as `(f(x) == y)` no longer ends at the space
    after the inner `)`.
  - Attributes after `a(href="x")` no longer stop the template with
    "Missing hash key: ')'".
- A compile error in a template's code names the template's line.

## Development

```sh
iyi test
```

`slang_test.iyi` holds the tests of the Crystal shard's `spec/slang_spec.cr`,
with their templates under `spec/`, and the port's own additions. The module
is `slang.iyi` (what rendered code needs at run time, and the macros) and
`slang/process.iyi` (the lexer, parser and code generation the macros run at
compile time).

## Thanks

Slang exists because of the people who wrote and kept it alive:

- [Jerome Gravel-Niquet](https://github.com/jeromegn) created Slang in 2016
  and maintained it as [jeromegn/slang](https://github.com/jeromegn/slang).
- [Todd Sundsted](https://github.com/toddsundsted) maintained the fork
  [toddsundsted/slang](https://github.com/toddsundsted/slang) from 2020 to
  2026 and made Slang 2.0: Slim's whitespace and escaping rules, blocks,
  `case … in`, splat attributes and a thorough test suite. This port follows
  his code closely.
- Everyone else who contributed: [Dmitry Neveshkin](https://github.com/kRaw1er),
  [Anton Maminov](https://github.com/mamantoha),
  [Isaac Sloan](https://github.com/elorest), Cris Ward,
  [Florin Lipan](https://github.com/lipanski), [Ivan](https://github.com/janczer),
  Sergey Makridenkov, SlayerShadow, [TSUYUSATO Kitsune](https://github.com/makenowjust),
  [V. Elenhaupt](https://github.com/veelenga), beno and
  [nashimoto](https://github.com/nashimoto).

Their history is in this repository's git log.

## License

MIT, see [LICENSE](LICENSE).
