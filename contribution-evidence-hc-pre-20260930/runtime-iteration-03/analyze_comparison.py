"""Pool every measured sample and expose all six round medians per arm."""
import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


def percentile(values,fraction):
    values=sorted(values);position=(len(values)-1)*fraction
    lower=math.floor(position);upper=math.ceil(position)
    return values[lower]+(values[upper]-values[lower])*(position-lower)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',nargs=2,type=Path,required=True)
    parser.add_argument('--candidate',nargs=2,type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--label',required=True)
    args=parser.parse_args()
    baselines=[json.loads(path.read_text()) for path in args.baseline]
    candidates=[json.loads(path.read_text()) for path in args.candidate]
    all_runs=baselines+candidates
    assert all(len(run['cases'])==28 for run in all_runs),'incomplete result cannot be compared'
    assert len({run['timing'] for run in all_runs}) == 1
    timing = all_runs[0]['timing']
    rows=[]
    for index in range(28):
        items=[run['cases'][index] for run in all_runs]
        key=items[0]['case'];assert all(item['case']==key for item in items)
        assert all(item['input_sha256'] == items[0]['input_sha256'] for item in items)
        arms=[]
        for runs,group in ((baselines,items[:2]),(candidates,items[2:])):
            measured=[];round_medians=[];process_medians=[]
            for run,item in zip(runs,group,strict=True):
                values=[]
                for round_data in item['rounds']:
                    samples=round_data['event_us'][run['warmup']:]
                    assert len(samples)==run['samples']
                    values.extend(samples);round_medians.append(statistics.median(samples))
                measured.extend(values);process_medians.append(statistics.median(values))
            arms.append({'median_us':statistics.median(measured),'p10_us':percentile(measured,.1),'p90_us':percentile(measured,.9),
                         'round_medians_us':round_medians,'process_medians_us':process_medians,'samples':len(measured)})
        base,candidate=arms
        rows.append({'case':key,'baseline':base,'candidate':candidate,'speedup':base['median_us']/candidate['median_us'],
                     'latency_change_percent':(candidate['median_us']/base['median_us']-1)*100,
                     'pair_speedups':[a/b for a,b in zip(base['process_medians_us'],candidate['process_medians_us'],strict=True)],
                     'serialized_output_hashes_equal':len({item['output_sha256'] for item in items})==1})
    result={'label':args.label,'scope':f'Complete HcPre {timing} operator; no model throughput claim','statistical_scope':'Two independent processes per arm; no iid confidence interval claimed',
            'sources':[{'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in (*args.baseline,*args.candidate)],
            'geometric_mean_speedup':math.exp(statistics.mean(math.log(row['speedup']) for row in rows)),
            'pair_geometric_mean_speedups':[math.exp(statistics.mean(math.log(row['pair_speedups'][i]) for row in rows)) for i in (0,1)],
            'faster':sum(row['speedup']>1 for row in rows),'slower':sum(row['speedup']<1 for row in rows),'max_slowdown_percent':max(row['latency_change_percent'] for row in rows),
            'cases':rows}
    args.output.write_text(json.dumps(result,indent=2))
    print({k:v for k,v in result.items() if k not in ('sources','cases')})
    for row in rows:print(row['case'],round(row['latency_change_percent'],3),[round(v,5) for v in row['pair_speedups']],row['serialized_output_hashes_equal'])

if __name__=='__main__':main()
