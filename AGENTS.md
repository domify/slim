# Working on Slang

Slang is a native iyi module: Slim-style templates, ported from the
Crystal shard Slang 2.0.3. To write templates in a project that uses Slang,
read [TEMPLATES.md](TEMPLATES.md) instead; this page is for changing Slang
itself.

## Layout

- `slang.iyi` is what rendered code needs at run time (`Slang.escape`,
  `Slang.attribute`, …) and the `render` / `embed` macros.
- `slang/process.iyi` is the lexer, parser and code generation. The macros
  run it at compile time; it prints the iyi source that renders a template.
- `slang_test.iyi` runs every template under `spec/` and compares the HTML.
- `archive/crystal/` is the Crystal original, kept as a reference. Do not
  change it.

## Checks

```sh
iyi test
iyi build slang_test.iyi --emit-iyimod /tmp/iyimod -o /tmp/slang_test
```

CI runs both. The second fails when an exported `def` is not fully typed:
a consumer reads the module's surface from its `.iyimod`. Use `forall` for
generic parameters.

## Rules

- A change of behaviour gets a template under `spec/`, a case in
  `slang_test.iyi`, and a line in the README's "Differences from Crystal
  Slang 2.0.3" when it departs from the original.
- Keep the syntax table in the README, the header comment of `slang.iyi` and
  [TEMPLATES.md](TEMPLATES.md) in step with the code.
- Template errors name the template's line: `raise "slang: … at line
  #{@line_number}, column #{@column_number}"`.
- Follow the original's code closely where nothing needs fixing; it keeps
  the port comparable to `archive/crystal/`.
