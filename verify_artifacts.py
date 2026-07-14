import os, json

datasets = ['nslkdd', 'ciciot', 'unswnb15', 'cicids2017']
print('=== FINAL ARTIFACT CHECK ===')
for ds in datasets:
    path = f'backend/artifacts/{ds}_meta.json'
    if os.path.exists(path):
        with open(path) as f:
            meta = json.load(f)
        best = max(meta['metrics'], key=lambda x: x['f1'])
        print(f'OK  {ds:<12} F1={best["f1"]}%  AUC={best["auc"]}%')
    else:
        print(f'MISSING: {ds}')
