from pathlib import Path
base = Path(r'D:\harness office\research\jobtask-agent\gh_publish')
for sub in ['scripts', 'docs']:
    d = base / sub
    print(f'=== {sub} ===')
    for f in sorted(d.iterdir()):
        print(f'  {f.name}')
    print()
