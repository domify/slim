# Slim

Lightweight, terse templates for ris, in the syntax of
[Slim](https://github.com/slim-template/slim).

This module continues [Slang](https://github.com/toddsundsted/slang), a
Slim-style template language for Crystal that started in 2016. The lexer,
parser and code generation of Slang's last release (2.0.3) are ported to ris,
along with its tests, and the port is named Slim after the syntax it follows.
The Crystal code is kept unchanged in [`archive/crystal/`](archive/crystal/)
and is no longer maintained. The ris port is maintained by Priit Tark at
[domify](https://github.com/domify).

Like the original, a template is turned into ris code at compile time, so a
rendered page is ordinary compiled code by the time the program runs.

## Installation

Add it to a consuming project's `ris.mod`; `ris` fetches the tag from GitHub:

```text
require github.com/domify/slim v0.3.0
```

## Usage

```ruby
import github.com/domify/slim::{Slim}

def page(name : String, items : Array(String)) : TapeString
  Slim.render("views/page.slim")
end

Tape.scope do
  body = page("Mari", ["one", "two"])
  # Consume body.to_unsafe / body.bytesize synchronously in this scope.
end
```

`Slim.render(filename, capacity = 256)` returns a `TapeString` owned by the
caller's active `Tape.scope`. There is one internal renderer and one tape
buffer; Slim has no heap-buffer renderer. Without a scope, tape allocation
terminates with a diagnostic. The compiler rejects returning or storing the
tape result beyond its owning scope. Raw pointers remain the caller's
responsibility.

For an ordinary retained `String`, use the explicit conversion API:

```ruby
def retained_page(name : String, items : Array(String)) : String
  Slim.render_string("views/page.slim")
end
```

Inside an existing scope, `Slim.render("views/page.slim").to_s` makes the
same retained copy directly. `render_string` is the convenience spelling
that manages an independent temporary tape.

`render_string(filename, capacity = 256)` uses the same tape renderer and
copies its output before returning. It always uses `local_tape`, independently
of any caller's `Tape.scope`, and releases its temporary buffers immediately.
The runtime can reuse that memory on the next call. Outer `TapeString` values
may be read by the template. Convert other outer tape values to owned data
before calling `render_string`; the compiler refuses access to them inside
`local_tape` to prevent references to temporary storage escaping.

`Slim.embed(filename, io)` writes directly to a supplied writer implementing
`<<`. This includes `Slim::TapeBuffer.new(capacity)` in a tape scope and an
explicitly supplied `String::Builder`. A sink may implement `text(String)` (instead of `<<`),
`emit(value)`, `raw(value)` and `capture { ... }` to supply its own text,
escaping, safe-value and capture semantics. Helper blocks write into
the same sink when it has `capture` and return that capture result;
otherwise they use `String.build`. Attributes always escape their values.
A tape buffer's `finish` returns a
borrowed `TapeString`; `to_s` makes a retained String copy. Do not append or
grow that buffer after taking a view of its bytes.

Paths are relative to the source file calling the macro, or used as written
when absolute. Templates see the calling method's local variables.

A method returning borrowed HTML declares `: TapeString`; a retained
String declares `: String`. Calling `.to_s` on TapeString copies its bytes
into an independent String. Caches and other retained destinations accept
String, so this boundary is checked by the compiler. Domain methods keep
domain names, without tape/heap prefixes on every call.

Rendering now streams escaped bytes and class names into the sink instead
of collecting fragments, escaped byte arrays or joined class strings.
Escaped and raw `TapeString` values and 8–64-bit integer output avoid
intermediate heap strings. Interpolated expressions forming a String,
non-integer `to_s`, and default HTML block captures may allocate on the heap.

[TEMPLATES.md](TEMPLATES.md) is a short guide to writing templates, for
agents and people who know Slim; [AGENTS.md](AGENTS.md) is for working on
Slim itself.

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

With `title = "Slim"`, `name = "<world>"`, `items = ["one", "two"]` and
`current = "two"`, this renders as (one line, broken here for reading):

```html
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Slim</title>
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
| `- code` | ris code: `if`/`elsif`/`else`, `case`/`when`/`in`, `each do`, assignments. |
| `/ text`, `/! text`, `/[if IE]` | An invisible, a visible and a conditional comment. |
| `javascript:`, `css:` | A `script` or `style` element with verbatim text. |
| `ris:`, `iyi:`, `crystal:` | Lines of ris code. |
| `~ "\n  "` | A quoted ris string, written exactly (including whitespace). |
| `doctype html` | `<!DOCTYPE html>`. |

As in Slim, there is no whitespace between tags. An attribute value without
quotes ends at the first space outside parentheses or brackets, so compute a
long expression in a `- name = …` line first. For the same reason, output
after such a value needs a space before its `=`, as in `li class=css = item`;
after a tag or a quoted value, `p= name` and `a href="/"= name` need none.

## Differences from Crystal Slang 2.0.3

- `~ "\n  "` writes a quoted ris string exactly, with ris escape sequences.
  Use it for explicit newlines and indentation when matching existing HTML.
- Custom sinks may define `text`, `emit`, `raw` and `capture` hooks; helper
  blocks receive the sink's capture result, a String by default.
- Raw output is `!=`, as in Haml and Pug, so it does not read as a
  comparison; `==` stops the template with an error.
- An attribute whose value is `false` or `nil` is left out and `true` writes
  the bare name, including `id` and the entries of a `*splat` hash.
- Blank class names are left out, and an element without a class name has no
  `class` attribute.
- `ris:` opens a code block; `iyi:` and `crystal:` remain compatible aliases.
- `begin`/`rescue` lines are parsed, but ris has no exceptions, so they do not
  compile. Kilt and Kemal's `content_for` are not supported.
- `render` returns `TapeString` in a caller-owned `Tape.scope`. Use
  `render_string` for an independent `String`. Both render through tape;
  `render_tape`, `render_heap` and the former `Buffer` class are removed.
- `render_string` always uses an independent `local_tape` and releases its
  temporary buffers before returning, including inside a caller's scope.
- Splat expressions are evaluated once per element, after explicit class
  expressions and before ordinary attributes.
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
./check.sh
```

`slim_test.ri` holds the tests of the Crystal shard's `spec/slang_spec.cr`,
with their templates under `spec/`, and the port's own additions. The module
is `slim.ri` (what rendered code needs at run time, and the macros) and
`slim/process.ri` (the lexer, parser and code generation the macros run at
compile time).

Runtime benchmarks comparing iyi, ris, builder and tape output are in
[`bench/`](bench/README.md). They do not change the public rendering API.

## Thanks

Slim exists because of the people who wrote and kept it alive:

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
