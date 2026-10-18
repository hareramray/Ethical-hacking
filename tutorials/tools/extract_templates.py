"""Extract every source template and reference table without changing its text."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'roadmaps/27-reusable-templates-and-glossary.md'
DEST = ROOT / 'tutorials/templates'
NAMES = {
    'Learning note template': 'learning-note.md',
    'Scope and rules-of-engagement template': 'scope-and-roe.md',
    'Finding template': 'finding.md',
    'Test-case record': 'test-case.md',
    'Hypothesis record': 'hypothesis.md',
    'Remediation verification record': 'retest.md',
    'Weekly learning review': 'weekly-review.md',
}
TABLES = {
    'Coverage and progress templates': 'coverage-and-progress.md',
    'Evidence register': 'evidence-register.md',
    'Change and cleanup register': 'change-and-cleanup-register.md',
    'Glossary': 'glossary.md',
}


def main():
    text = SOURCE.read_text(encoding='utf-8')
    # Real headings only: templates themselves also contain Markdown headings.
    lines = text.splitlines()
    sections = {}
    current = None
    fenced = False
    for line in lines:
        if line.startswith('```'):
            fenced = not fenced
        heading = re.match(r'^#{2,3} (.+)$', line) if not fenced else None
        if heading:
            current = heading.group(1)
            sections[current] = []
        elif current:
            sections[current].append(line)
    DEST.mkdir(parents=True, exist_ok=True)
    for title, filename in NAMES.items():
        section = '\n'.join(sections[title])
        match = re.search(r'```markdown\n(.*?)\n```', section, re.S)
        if not match:
            raise ValueError(f'Missing template: {title}')
        (DEST / filename).write_text(match.group(1) + '\n', encoding='utf-8')
    for title, filename in TABLES.items():
        (DEST / filename).write_text('# ' + title + '\n\n' + '\n'.join(sections[title]).strip() + '\n', encoding='utf-8')
    index = ['# Reusable templates and glossary', '', '[Tutorial index](../README.md) | [How to fill these templates](../27-reusable-templates-and-glossary.md)', '', 'All seven fenced Markdown templates and four table/reference sections are extracted from the original chapter without paraphrasing. Copy a blank into your private exercise directory and fill it with evidence; these are document templates, not installed Codex skills.', '']
    index += [f'- [{title}]({filename})' for title, filename in {**NAMES, **TABLES}.items()]
    index += ['', 'Regenerate only when intentionally updating the source: `python tutorials/tools/extract_templates.py`. This overwrites the reusable blank files, so keep completed records elsewhere.', '']
    (DEST / 'README.md').write_text('\n'.join(index), encoding='utf-8')
    print(f'Extracted {len(NAMES)} complete templates and {len(TABLES)} reference/table sections.')


if __name__ == '__main__':
    main()
