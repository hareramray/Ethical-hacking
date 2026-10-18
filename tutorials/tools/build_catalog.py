"""Build tutorial navigation and an auditable, complete curriculum mirror.

Run from any directory: python tutorials/tools/build_catalog.py
Validate without writing: python tutorials/tools/build_catalog.py --check
Only catalog files and curriculum mirrors are generated; lessons are hand-authored.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import os
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'roadmaps'
DEST = ROOT / 'tutorials'
LINK = re.compile(r'(?<!!)\[([^\]\n]*)\]\(([^)\n]+)\)')


def without_code(text):
    result = []
    fence = None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker[0]
            elif marker[0] == fence:
                fence = None
            continue
        if fence is None:
            result.append(line)
    return '\n'.join(result)


def rebased(source):
    """Keep all text; redirect relative links for the curriculum's new location."""
    target = DEST / 'curriculum' / source.relative_to(SOURCE)
    def replace(match):
        label, address = match.groups()
        if address.startswith(('#', 'https:', 'http:', 'mailto:')):
            return match.group(0)
        path, sep, anchor = address.partition('#')
        original = (source.parent / unquote(path)).resolve()
        if original.is_relative_to(SOURCE):
            original = DEST / 'curriculum' / original.relative_to(SOURCE)
        new = Path(os.path.relpath(original, target.parent)).as_posix()
        return f'[{label}]({new}{sep}{anchor})'
    return LINK.sub(replace, source.read_text(encoding='utf-8'))


def headings(text):
    seen = Counter()
    for line in without_code(text).splitlines():
        match = re.match(r'^(#{2,6}) (.+)$', line)
        if match and match.group(2) != 'Contents':
            title = match.group(2)
            slug = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
            count = seen[slug]
            seen[slug] += 1
            yield title, slug + (f'-{count}' if count else '')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    sources = sorted(SOURCE.rglob('*.md'))
    topics = [p for p in sources if re.match(r'^\d\d-', p.name)]
    errors = []
    records = []
    for source in sources:
        output = DEST / 'curriculum' / source.relative_to(SOURCE)
        expected = rebased(source)
        if args.check:
            if not output.exists() or output.read_text(encoding='utf-8') != expected:
                errors.append(f'Curriculum mismatch: {output.relative_to(ROOT)}')
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(expected, encoding='utf-8')
        if source not in topics:
            continue
        relative = source.relative_to(SOURCE).as_posix()
        text = source.read_text(encoding='utf-8')
        title = text.splitlines()[0].removeprefix('# ')
        lesson = DEST / relative
        if args.check and not lesson.exists():
            errors.append(f'Missing tutorial: {relative}')
        records.append({'topic': title, 'tutorial': relative,
                        'source': source.relative_to(ROOT).as_posix(),
                        'curriculum': 'curriculum/' + relative,
                        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'checklist_items': len(re.findall(r'^\s*- \[[ xX]\]', text, re.M)),
                        'headings': list(headings(text))})
    if len(records) != 36:
        errors.append(f'Expected 36 numbered topic sources; found {len(records)}')
    count = sum(record['checklist_items'] for record in records)
    if not args.check:
        (DEST / 'coverage-manifest.json').write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        rows = '\n'.join(f"| [{r['topic']}]({r['tutorial']}) | [Full curriculum]({r['curriculum']}) | {r['checklist_items']} |" for r in records)
        readme = f'''# Ethical hacking tutorials

Created 18 October 2026. **36 tutorials: 28 main chapters and 8 specialist tracks.**

Start with [00: how to learn](00-how-to-use-this-roadmap.md), then [01: scope](01-authorization-scope-and-professional-conduct.md) and [02: lab setup](02-build-a-safe-repeatable-lab.md). Continue through 03–16, practice detection (20) and reporting (23) throughout, then choose a specialization. Chapters 24–27 turn the work into projects, a schedule, tool fluency, and reusable notes.

Each tutorial teaches the mechanisms, works through concrete examples, and asks you to collect evidence and check the result. Examples use owned, isolated systems, synthetic records, or offline simulations. Run the commands only in the environment named in the lesson. Do not paste Linux shell commands into PowerShell or assume a simulated control proves a real device is secure.

## What is included

- [Runnable local examples](examples/README.md): a loopback-only API, synthetic event analysis, and a bounded parser exercise, using Python's standard library.
- [Reusable templates](templates/README.md): editable notes, scope, tests, findings, evidence, changes, retests, reviews, and coverage tables.
- [Every source subheading](TOPIC_INDEX.md): a drill-down index into the complete curriculum.
- [Coverage and validation](COVERAGE.md): the exact source mapping and reproducible checks.
- [Progress tracker](PROGRESS.md): record evidence and proficiency independently of reading completion.

The complete expanded curriculum is retained for each chapter: **{count} checklist occurrences**, including intentional overlap between the specialization overview and its leaf chapters. The source headings, prose, tables, projects, templates, glossary, and references are preserved; only relative links are relocated. The companion tutorial is the teaching layer. Retention checks establish that no source material was dropped; they do not certify mastery or exhaustive treatment of all security research.

## Chapters

| Tutorial | Original curriculum retained | Checklist occurrences |
| --- | --- | ---: |
{rows}

## Study one lesson

1. Read the prerequisites and explanation. Predict the expected result before running an example.
2. Build the specified disposable environment and record its versions and recovery method.
3. Complete the guided example, then change one assumption and explain the outcome.
4. Save a sanitized observation, a root-cause explanation, a correction, and a repeatable retest.
5. Review the linked curriculum checklist and expanded modules. Track remaining subtopics explicitly.
6. Rebuild or reproduce independently before recording practical competence.

## Validate the collection

From the repository root, run `python tutorials/tools/build_catalog.py --check`. This checks all 36 tutorial paths, complete curriculum retention, manifest freshness, and local Markdown file links. Run `python tutorials/examples/check_examples.py` for the portable worked examples. Neither command performs external scanning or installs software. Hardware, VM, platform, and paid-service exercises require their named environments and are not automatically executed.
'''
        (DEST / 'README.md').write_text(readme, encoding='utf-8')
        index = ['# Topic and subtopic index', '', '[Tutorial index](README.md)', '', 'Every source heading outside fenced examples is listed below. Fenced templates and all checklist text remain in the complete curriculum. Each heading links to its retained source section; use the chapter tutorial for the worked teaching sequence.', '']
        for record in records:
            index += [f"## {record['topic']}", '', f"[Tutorial]({record['tutorial']}) | [Complete curriculum]({record['curriculum']})", '']
            index += [f"- [{title}]({record['curriculum']}#{slug})" for title, slug in record['headings']]
            index.append('')
        (DEST / 'TOPIC_INDEX.md').write_text('\n'.join(index), encoding='utf-8')
        coverage = f'''# Coverage and validation

[Tutorial index](README.md) | [Subtopic index](TOPIC_INDEX.md)

The collection has one authored tutorial for each of the **36 numbered roadmap files**. All **{count} checklist occurrences** across those files remain in their complete curriculum companions, together with every other paragraph, heading, example, table, and reference. The overview and specialization leaf files intentionally repeat some subjects. Supporting roadmap README, COVERAGE, and PROGRESS documents are also mirrored.

| Source topic | Retained curriculum | Checklist occurrences |
| --- | --- | ---: |
{rows}

`coverage-manifest.json` records each source file's SHA-256, relative tutorial path, checklist count, and source headings. `tools/build_catalog.py --check` compares each retained document against the complete source after deterministic relative-link relocation. It also checks manifest freshness and local Markdown file targets outside fenced examples. This is a structural preservation check, not an automated proof of pedagogical depth, factual accuracy, or working external links.

Regenerate the catalog after intentionally changing a source using `python tutorials/tools/build_catalog.py`, then run `--check`. Regeneration never overwrites authored tutorials or an existing learner progress tracker. Original files in `roadmaps/` are not modified.

Portable examples are checked by `python tutorials/examples/check_examples.py`: authorization before/after behavior, loopback HTTP status/body behavior, event correlation including a near-name negative control, strict parser boundary handling, and a bounded deterministic corpus. VM, Android/iOS, radio, hardware, cloud, and compiler exercises are environment-specific and are not represented as executed by these checks.
'''
        (DEST / 'COVERAGE.md').write_text(coverage, encoding='utf-8')
        progress = DEST / 'PROGRESS.md'
        if not progress.exists():
            progress.write_text('# Tutorial progress\n\n[Start here](README.md)\n\nLevels: 0 new; 1 can explain; 2 guided demonstration; 3 independent reproduction and repair; 4 extends/reviews. Reading completion is separate from proficiency. Record limitations and unfinished subtopics.\n\n| Topic | Level | Evidence | Next subtopic | Last practiced |\n| --- | --- | --- | --- | --- |\n' + '\n'.join(f"| [{r['topic']}]({r['tutorial']}) | 0 | | | |" for r in records) + '\n', encoding='utf-8')
    else:
        manifest = DEST / 'coverage-manifest.json'
        if not manifest.exists() or json.loads(manifest.read_text(encoding='utf-8')) != [dict(r, headings=[list(h) for h in r['headings']]) for r in records]:
            errors.append('Coverage manifest is missing or stale; regenerate catalog.')
        for file in DEST.rglob('*.md'):
            content = without_code(file.read_text(encoding='utf-8'))
            for _, target in LINK.findall(content):
                if target.startswith(('#', 'https:', 'http:', 'mailto:', 'app:')):
                    continue
                path = unquote(target.split('#', 1)[0].strip('<>'))
                if path and not (file.parent / path).exists():
                    errors.append(f'Broken local link in {file.relative_to(DEST)}: {target}')
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print(f'{"Validated" if args.check else "Generated"}: {len(records)} topics, {count} checklist occurrences, {len(sources)} complete curriculum files.')


if __name__ == '__main__':
    main()
