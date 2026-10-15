#!/usr/bin/env python3
"""Compile identical Slang workloads, verify bytes, measure shuffled rounds."""
import argparse, hashlib, json, os, platform, random, statistics, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IYI = ROOT.parents[1] / 'iyis/slang'
TEMPLATES = {
    'text': '''doctype html
html
  body
    h1= title
    ul
      - items.each do |item|
        li= item
''',
    'attributes': '''doctype html
html lang="et"
  body
    h1.title= title
    ul#items
      - items.each do |item|
        li.row class=css data-name=item
          a href=item title=title = item
''',
}

def heap_only_runtime(source):
    """Same optimized heap implementation, without ris-only tape APIs."""
    start = source.index("  # Owned by the caller's Tape.scope")
    end = source.index('  # Keep the <<-only sink contract.', start)
    source = source[:start] + source[end:]
    for signature in [
        '  def self.write_raw(buffer : B, value : TapeString)',
        '  def self.write_escaped(buffer : B, value : TapeString)',
    ]:
        start = source.index(signature)
        end = source.index('\n  end', start) + len('\n  end')
        source = source[:start] + source[end:]
    source = source.replace(' | TapeBuffer', '').replace('String | TapeString', 'String')
    old_escape = """        result = ""
        Tape.scope do
          buffer = TapeBuffer.new(text.bytesize)
          write_escaped(buffer, text)
          result = buffer.to_s
        end
        return result"""
    new_escape = """        buffer = String::Builder.new(text.bytesize)
        write_escaped(buffer, text)
        return buffer.to_s"""
    assert old_escape in source
    source = source.replace(old_escape, new_escape)
    start = source.index("  # The default result is borrowed")
    end = source.index('\nend', start)
    source = source[:start] + """  macro render(filename, capacity = 256)
    begin
      %buffer = ::String::Builder.new({{capacity}})
      ::Slang::Slang.embed({{filename}}, %buffer)
      %buffer.to_s
    end
  end

  macro render_string(filename, capacity = 256)
    ::Slang::Slang.render({{filename}}, {{capacity}})
  end
""" + source[end:]
    code = '\n'.join(line for line in source.splitlines() if not line.lstrip().startswith('#'))
    assert all(word not in code for word in ['TapeString', 'TapeBuffer', 'Tape.scope'])
    return source


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--include-iyi-optimized', action='store_true', help='Also compile the same optimized heap implementation with iyi')
    ap.add_argument('--skip-build', action='store_true', help='Reuse binaries from an unchanged previous build')
    ap.add_argument('--iterations', type=int, default=200000)
    ap.add_argument('--rounds', type=int, default=7)
    ap.add_argument('--build-dir', type=Path, default=Path('/tmp/slang-tape-first-bench'))
    a = ap.parse_args()
    if a.iterations < 1 or a.rounds < 1:
        ap.error('iterations and rounds must be positive')
    build = a.build_dir.resolve(); build.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, IYI_CACHE_DIR=str(build/'cache'))
    rows = []
    modes = [('iyi','render'), ('iyi','builder'), ('ris','render'), ('ris','render_string'), ('ris','builder')]
    if a.include_iyi_optimized:
        modes += [('iyi','optimized-render'), ('iyi','optimized-builder')]
    for compiler, mode in modes:
        folder = build/f'{compiler}-{mode}'; folder.mkdir(exist_ok=True)
        ext = '.iyi' if compiler == 'iyi' else '.ri'
        optimized_iyi = mode.startswith('optimized-')
        src = ROOT if optimized_iyi or compiler == 'ris' else IYI
        source_ext = '.ri' if optimized_iyi or compiler == 'ris' else '.iyi'
        for rel in ['slang'+ext, 'slang/process'+ext, 'iyi.mod']:
            dest=folder/rel; dest.parent.mkdir(exist_ok=True)
            original = src/(rel.replace(ext, source_ext) if rel.endswith(ext) else rel)
            content = original.read_text()
            if optimized_iyi and rel == 'slang'+ext:
                content = heap_only_runtime(content)
            dest.write_text(content)
        for workload, template in TEMPLATES.items():
            (folder/(workload+'.slang')).write_text(template)
            body = 'html = Slang.render("'+workload+'.slang")\n    ptr = html.to_unsafe\n    size = html.bytesize'
            if mode.endswith('builder'):
                body = 'html = String.build do |buf|\n      Slang.embed("'+workload+'.slang", buf)\n    end\n    ptr = html.to_unsafe\n    size = html.bytesize'
            elif mode == 'render_string':
                body = 'html = Slang.render_string("'+workload+'.slang")\n    ptr = html.to_unsafe\n    size = html.bytesize'
            tape_scope = compiler == 'ris' and mode == 'render'
            consume = '''\n    bytes += size.to_i64
    k = 0
    while k < size
      checksum = (checksum ^ ptr[k].to_u64) &* 1099511628211_u64
      k += 1
    end'''
            code = '''module benchmark
import slang::{Slang}
title = "Tere <maailm> & café"
items = ["one", "two & three", "<four>", "viis", "kuus", "seitse", "kaheksa", "üheksa"]
css = "active & selected"
checksum = 14695981039346656037_u64
bytes = 0_i64
i = 0
while i < '''+str(a.iterations)+'''\n'''+('  Tape.scope do\n' if tape_scope else '')+'    '+body+consume+('\n  end' if tape_scope else '')+'''
  i += 1
end
puts "#{bytes} #{checksum}"
'''
            source=folder/(workload+ext); source.write_text(code)
            binary=folder/(workload+'-bin')
            start=time.perf_counter()
            if a.skip_build:
                manifest = folder/(workload+'-manifest.json')
                current = {str(f.relative_to(folder)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [source,folder/('slang'+ext),folder/('slang/process'+ext)]}
                if not manifest.exists() or json.loads(manifest.read_text()) != current:
                    raise RuntimeError('Cannot reuse a binary built from different sources: '+str(binary))
            if not a.skip_build:
                subprocess.run([compiler,'build','--release',str(source),'-o',str(binary)],cwd=folder,env=env,check=True)
            manifest = {str(f.relative_to(folder)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [source,folder/('slang'+ext),folder/('slang/process'+ext)]}
            (folder/(workload+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
            row={'compiler':compiler,'mode':mode,'workload':workload,'binary':str(binary),'build_s':None if a.skip_build else time.perf_counter()-start,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'module_sources_sha256':manifest,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'runs':[],'failures':[]}
            rows.append(row)
            print('reused' if a.skip_build else 'built',compiler,mode,workload,flush=True)
    expected={}
    for round_no in range(a.rounds+1):
        shuffled=rows.copy(); random.Random(842+round_no).shuffle(shuffled)
        for row in shuffled:
            usage=build/'usage.txt'
            p=subprocess.run(['/usr/bin/time','-f','%e %U %S %M','-o',str(usage),row['binary']],capture_output=True,text=True)
            if p.returncode:
                row['failures'].append({'round':round_no,'returncode':p.returncode,'stderr':p.stderr})
                print('FAILED', row['compiler'], row['mode'], row['workload'], p.returncode, flush=True)
                continue
            output=p.stdout.strip(); key=row['workload']
            if key in expected and expected[key]!=output:
                raise RuntimeError(f'Output mismatch: {row}: {output} != {expected[key]}')
            expected[key]=output
            wall,user,system,rss=map(float,usage.read_text().split())
            if round_no:
                row['runs'].append({'wall_s':wall,'user_s':user,'sys_s':system,'rss_kib':rss})
        (build/'partial.json').write_text(json.dumps(rows,indent=2)+'\n')
        print('round',round_no,'complete',flush=True)
    for row in rows:
        row['median_s']=statistics.median(r['wall_s'] for r in row['runs']) if row['runs'] else None
        row['median_rss_kib']=statistics.median(r['rss_kib'] for r in row['runs']) if row['runs'] else None
    result={'platform':platform.platform(),'cpu':next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), 'unknown'),'iterations':a.iterations,'rounds':a.rounds,'outputs':expected,'versions':{c:subprocess.check_output([c,'version'],text=True).strip() for c in ['iyi','ris']},'rows':rows}
    (build/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    for row in rows:
        print(row['workload'],row['compiler'],row['mode'],row['median_s'],row['median_rss_kib'])
    print('results:',build/'results.json')
    if any(row['failures'] for row in rows):
        raise SystemExit(1)
if __name__=='__main__': main()
