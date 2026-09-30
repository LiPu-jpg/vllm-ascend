import csv, json, statistics, sqlite3
from pathlib import Path
root=Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-01')
summary=[]
for path in sorted(root.glob('profile-*/data/*/*/ASCEND_PROFILER_OUTPUT/kernel_details.csv')):
    with path.open() as stream:
        rows=[r for r in csv.DictReader(stream) if r['Type']=='HcPre']
    item={'run':path.parts[-6], 'case':path.parts[-4], 'count':len(rows), 'csv':str(path)}
    for key in ['Duration(us)','Wait Time(us)','aicore_time(us)','aiv_time(us)','aiv_vec_time(us)','aiv_scalar_time(us)','aiv_mte2_time(us)','aiv_mte3_time(us)']:
        vals=[float(r[key]) for r in rows if r.get(key)]
        item[key]={'median':statistics.median(vals),'min':min(vals),'max':max(vals)} if vals else None
    db=path.parent/'ascend_pytorch_profiler.db'
    if db.exists():
        with sqlite3.connect(db) as conn:
            tables=[r[0] for r in conn.execute("select name from sqlite_master where type='table'")]
            item['db_counts']={name:conn.execute('select count(*) from "'+name+'"').fetchone()[0] for name in tables if name in ('CANN_API','PYTORCH_API','TASK','STRING_IDS')}
    summary.append(item)
(root/'profile-summary.json').write_text(json.dumps(summary,indent=2))
for item in summary:
    print(item['run'],item['case'],item['count'],*[round(item[k]['median'],3) if item[k] else None for k in ('Duration(us)','aiv_time(us)','aiv_vec_time(us)','aiv_scalar_time(us)','aiv_mte2_time(us)','aiv_mte3_time(us)')])
