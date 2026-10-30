import pandas as pd, math

j = pd.read_parquet('out/objects/judge_g2_2020.parquet')
comm = pd.read_parquet('out/objects/g2_comm_2020.parquet')
lab = pd.read_parquet('out/objects/labels_g2_2020.parquet')
for df in [j, comm, lab]:
    df['seed'] = df['seed'].astype(str)
m = j.merge(comm[['seed', 'hier_n']], on='seed').merge(lab[['seed', 'h', 'split']], on='seed')
m['holds_new'] = ((m['holds'] == 1) & (m['hier_n'] >= 3)).astype(int)

for label, col in [('原', 'holds'), ('新', 'holds_new')]:
    for h, g in m.groupby('h'):
        a = len(g[(g[col] == 1) & (g['split'] == 1)])
        b = len(g[(g[col] == 1) & (g['split'] == 0)])
        c = len(g[(g[col] == 0) & (g['split'] == 1)])
        d = len(g[(g[col] == 0) & (g['split'] == 0)])
        n = a + b + c + d
        denom = (a + b) * (c + d) * (a + c) * (b + d)
        chi2 = (a * d - b * c) ** 2 * n / denom if denom > 0 else 0
        p = math.erfc(math.sqrt(chi2 / 2))
        print(f'{label} h={h}: chi2={chi2:.1f} p={p:.2e} n1={a+b}')
