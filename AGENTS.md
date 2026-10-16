# Working on Slim

Slim is a native ris module: Slim-style templates, ported from the
Crystal shard Slang 2.0.3. To write templates in a project that uses Slim,
read [TEMPLATES.md](TEMPLATES.md) instead; this page is for changing Slim
itself.

## Layout

- `slim.ri` is what rendered code needs at run time (`Slim.escape`,
  `Slim.attribute`, …) and the `render` / `render_string` / `embed` macros.
- `slim/process.ri` is the lexer, parser and code generation. The macros
  run it at compile time; it prints the ris source that renders a template.
- `slim_test.ri` runs every template under `spec/` and compares the HTML.
- `archive/crystal/` is the Crystal original, kept as a reference. Do not
  change it.

## Checks

```sh
./check.sh
```

This runs the original fixtures through default tape output and retained
String output (including one-byte tape buffer growth), sink/escaping/numeric/splat regression checks, an exported
module build and consumer, compiler refusals for escaping tape results, and the missing-scope diagnostic.
Exported `def`s must be fully typed; use `forall` for generic parameters.
`bench/run.py` compares the unchanged iyi source with this ris port. Compile
all benchmark variants before starting sequential, shuffled measurements.

## Rules

- `render` is the TapeString API; `render_string` copies the same tape output
  into an independent String using `to_s`. Keep borrowed return types
  explicit; retained destinations accept String. Do not add a separate heap
  renderer or tape/heap aliases.

- A change of behaviour gets a template under `spec/`, a case in
  `slim_test.ri`, and a line in the README's "Differences from Crystal
  Slang 2.0.3" when it departs from the original.
- Keep the syntax table in the README, the header comment of `slim.ri` and
  [TEMPLATES.md](TEMPLATES.md) in step with the code.
- Template errors name the template's line: `raise "slim: … at line
  #{@line_number}, column #{@column_number}"`.
- Follow the original's code closely where nothing needs fixing; it keeps
  the port comparable to `archive/crystal/`.
