"""Weekly signal-health check for the review committee (analysis only; trades nothing).

    python3 -W ignore research/committee/signal_health.py

Rank IC (Spearman) of each council researcher, the blended council and plain 12-1 momentum
against forward returns over the last ~250 trading days of the rolling window, by horizon,
by size tercile (60-day median traded value) and F&O vs non-F&O. Non-overlapping samples;
t-stats are rough (few observations, many comparisons: expect some |t|~2 by chance).
Writes research/committee/signal_health_<date>.md.
"""
import io, contextlib, os
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    import sys,json,numpy as np,pandas as pd; sys.path.insert(0,'.')
    from alpha.council_panel import CouncilPanel, RESEARCHERS
    from alpha import grammar
    from alpha.grammar import evaluate
    from alpha.scoring import zrank
    grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
    P=CouncilPanel(); m=P.mask; dates=P.dates; N=list(P.names)
    p=pd.read_pickle('data/bhav/panel.pkl'); A=p['adj']['close'][N].reindex(dates)
    tv=np.log(p['tv'][N].reindex(dates).rolling(60).median().values)
    pool=json.load(open('results/alpha_c_council_real.json'))
    comp={}
    for a in pool['alphas']:
        z=zrank(evaluate(a['seq'],P.feat),m)*a['weight']; comp[a['researcher']]=comp.get(a['researcher'],0)+z
    comp['COUNCIL']=sum(comp.values())
    comp['MOM12-1']=(A.shift(21)/A.shift(252)-1).values
    fo=np.isfinite(P.feat['basis']) if 'basis' in P.feat else None
    T=range(len(dates)-270,len(dates)-60)
    def ic(s,h,sel=None):
        f=(A.shift(-h)/A-1).values; out=[]
        for t in list(T)[::h]:
            ok=m[t]&np.isfinite(s[t])&np.isfinite(f[t])
            if sel is not None: ok&=sel[t]
            if ok.sum()>40: out.append(pd.Series(s[t][ok]).rank().corr(pd.Series(f[t][ok]).rank()))
        o=np.array(out); return f"{o.mean():+.3f} (t {o.mean()/o.std()*np.sqrt(len(o)):+.1f})"
    print('By horizon (all universe):')
    for k,s in comp.items(): print(f'  {k:9s}', ' '.join(f'{h}d {ic(s,h)}' for h in (5,20,60)))
    q=np.nanpercentile(np.where(m,tv,np.nan),[33,67],axis=1).T
    big=tv>=q[:,[1]]; small=tv<q[:,[0]]; mid=~big&~small
    print('By size, 20d:')
    for k,s in comp.items(): print(f'  {k:9s}', 'large',ic(s,20,big),' mid',ic(s,20,mid),' small',ic(s,20,small))
    if fo is not None:
        print('F&O vs non-F&O, 20d:')
        for k,s in comp.items(): print(f'  {k:9s}', 'F&O',ic(s,20,fo),' nonF&O',ic(s,20,~fo))
out = buf.getvalue(); print(out)
os.makedirs("research/committee", exist_ok=True)
d = str(P.dates[-1].date())
open(f"research/committee/signal_health_{d}.md", "w").write(f"# Signal health, {d}\n\nRank IC (t-stat) of each signal vs forward returns, last ~250 trading days.\n\n```\n{out}```\n")
