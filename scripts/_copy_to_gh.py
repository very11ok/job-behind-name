import shutil
from pathlib import Path
base = Path(r'D:\harness office\research\jobtask-agent')
gh = base / 'gh_publish'
copies = [
    ('verify_g3_fix.py', 'scripts/verify_g3_fix.py'),
    ('out/results/g3_fix_verify.md', 'docs/g3_fix_verify.md'),
]
for src, dst in copies:
    s, d = base / src, gh / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(s, d)
    print('copied', dst)

readme = gh / 'README.md'
text = readme.read_text(encoding='utf-8')
add = [
    ('scripts/verify_g3_fix.py', '原则三修复验证：客观规模前因（n_jobs/n_mod 组合）→ 模板采纳'),
    ('docs/g3_fix_verify.md', '原则三结果：组合前因提升比 2.98/3.26/3.06 全显著'),
]
lines = text.splitlines()
out, inserted = [], False
for ln in lines:
    out.append(ln)
    if not inserted and 'g2_direction_verify' in ln:
        for a, b in add:
            out.append(f'- `{a}` — {b}')
        inserted = True
if inserted:
    readme.write_text('\n'.join(out) + '\n', encoding='utf-8')
print('README updated:', inserted)
