# Slang runtime benchmark

```sh
python3 ~/contribute/ris/slang/bench/run.py
```

Current ris API:

- `render` returns TapeString and is measured in one Tape.scope per page.
- `render_string` renders to tape and copies to an independent String.
- `builder` is an explicit consumer-supplied String.build sink via embed.

There is no Slang heap Buffer class and no separate heap rendering path.
The unchanged iyi controls still use the original String-returning render.

For an additional generated heap-only algorithm control compiled with iyi:

```sh
python3 ~/contribute/ris/slang/bench/run.py --include-iyi-optimized \
  --build-dir /tmp/slang-tape-first-comparison
```

That control removes tape-specific types and overloads from benchmark
copies and writes directly to String::Builder. It is not production code.
The generated control also passes all 53 original iyi HTML fixtures.
Neither control edits the original iyis/slang module.

Needs iyi, ris, Python 3 and GNU /usr/bin/time. Generated files go in
/tmp/slang-tape-first-bench unless --build-dir is specified. --skip-build
requires matching source manifests and an unchanged compiler/prelude.

Defaults: 200,000 renders per execution, one excluded warm-up and seven
measured rounds. Every variant compiles with --release before sequential,
deterministically shuffled measurements. Median wall time has 0.01-second
resolution; RSS is median peak process RSS. JSON preserves every execution,
failures, source/binary hashes and compiler versions. Any failed execution
makes the command exit nonzero after writing its results.

Inputs are prepared once. The text page emits 220 bytes, the attribute page
1,187 bytes; each has eight items, UTF-8 and characters requiring escaping.
All output bytes are hashed with wrapping FNV-1a. Sizes and checksums must
agree across every implementation. Model construction, network I/O and
compilation time are excluded. Tape scope entry/exit and String copying
where applicable are included. Default Slang buffer capacity is 256 bytes;
the explicit String.build control uses the standard default capacity.

## Current API results (2026-10-16)

Fresh --release builds; 200,000 renders, one warm-up plus seven shuffled
measured rounds. All 112 executions passed and matched historical output
sizes/checksums. Full data: [results-current.json](results-current.json),
[current-run.log](current-run.log). No parallel builds ran during timing.

| Compiler / output | Text median, s | Attributes median, s | Peak RSS text / attributes, MiB |
|---|---:|---:|---:|
| iyi render | 0.24 | 1.52 | 5.78 / 5.78 |
| iyi builder | 0.14 | 1.10 | 5.66 / 5.53 |
| iyi optimized-render | 0.09 | 0.53 | 6.03 / 4.53 |
| iyi optimized-builder | 0.10 | 0.56 | 4.91 / 4.41 |
| ris render | 0.07 | 0.43 | 1.53 / 1.53 |
| ris render_string | 0.07 | 0.45 | 6.28 / 6.16 |
| ris builder | 0.08 | 0.49 | 4.82 / 4.41 |

Default tape render is about 3.4x / 3.5x faster than original iyi render
on these pages. Relative to the same optimized heap algorithm in iyi,
attribute-page throughput is about 1.23x higher. render_string includes its
final heap copy and takes 0.45 s versus tape render at 0.43 s. Small text
results round to the same 0.07 s at the timer's 0.01-second resolution;
this does not establish that copying has zero cost.

The workload isolates rendering and hashing prepared data; these are not
HTTP server or end-to-end request measurements. The clean run does not
diagnose or prove a fix for the intermittent crashes in historical series.

## Historical measurements

The retained result files below precede the tape-first API rename. Their
ris `render` rows used the former heap buffer; `tape-consume` corresponds to
today's `render`, and `tape-copy` to today's `render_string`. Do not interpret
old row names as current API behavior. New runs are needed for new timings.

- [results-iyi-ris.json](results-iyi-ris.json): original iyi, optimized iyi
  heap controls and optimized ris, including tape; full comparison.
- [comparison-run.log](comparison-run.log): one iyi optimized-builder
  attribute execution failed with SIGSEGV; six successful measured runs for
  that row, seven for all others. Successful outputs had matching checksums.
- [results.json](results.json), [final-run.log](final-run.log): preceding
  optimized series, including a non-tape ris builder SIGSEGV.
- [results-before.json](results-before.json): initial prototype comparisons.
- [results-exploratory.json](results-exploratory.json): exploratory timings
  that overlapped verification builds and are excluded from final numbers.
- [observed-failures.json](observed-failures.json),
  [failed-run.log](failed-run.log), [diagnostics.json](diagnostics.json):
  earlier intermittent crashes and debugger restrictions. No crash fix is
  claimed by the tape-first API change.

Run ../check.sh here for default tape and retained String fixture suites,
custom sinks, UTF-8/entities, integer boundaries, splat single evaluation,
exported module consumers, missing-scope diagnostics and lifetime refusals.
The lexer/parser remains compile-time heap work. Interpolations, class
String conversions, custom to_s methods and nested helper HTML may still
allocate on the heap. Nested Tape.scope blocks share the outer lifetime;
repeated render_string calls retain temporary buffers until that scope ends.
