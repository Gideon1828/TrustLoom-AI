"""Phase 1.1 - Audit existing dataset"""
import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path('d:/IVth Year Project/TrustLoom-AI/data/processed')
csv_files = list(data_dir.glob('lstm_dataset_*.csv'))
npy_labels = list(data_dir.glob('lstm_labels_*.npy'))

print('=== PHASE 1.1: EXISTING DATASET AUDIT ===')
print(f'CSV files found: {[f.name for f in csv_files]}')
print(f'Label .npy found: {[f.name for f in npy_labels]}')

expected_features = ['num_projects','experience_years','avg_duration','avg_overlap_score','skill_diversity','technical_depth']
old_feature_names = ['total_years','avg_project_duration','overlap_count','tech_consistency','project_link_ratio']

for f in csv_files:
    df = pd.read_csv(f)
    print(f'\n--- {f.name} ---')
    print(f'  Rows: {len(df)}')
    print(f'  Columns: {list(df.columns)}')

    if 'label' in df.columns:
        vc = df['label'].value_counts().sort_index()
        print(f'\n  Label Distribution:')
        for lbl, cnt in vc.items():
            print(f'    label={lbl}: {cnt} ({cnt/len(df)*100:.1f}%)')
        balance_ok = 0.45 <= vc.get(0,0)/len(df) <= 0.55
        print(f'    Balance (45-55%): {"PASS" if balance_ok else "FAIL"}')
        
        # Suspicious=1 check
        if 1 in vc:
            print(f'    suspicious=1 count: {vc[1]} -> {"OK" if vc[1]/len(df) >= 0.45 else "LOW"}')
        else:
            print(f'    WARNING: No label=1 found (suspicious class missing!)')

    print(f'\n  Feature Name Audit:')
    for feat in expected_features:
        status = 'OK' if feat in df.columns else 'MISSING (needs new generator)'
        print(f'    {feat}: {status}')
    for feat in old_feature_names:
        if feat in df.columns:
            print(f'    {feat}: OLD NAME (maps to wrong inference feature)')

    if 'fraud_pattern' in df.columns:
        print(f'\n  Fraud Patterns:')
        for pat, cnt in df['fraud_pattern'].value_counts().items():
            print(f'    {pat}: {cnt}')
    else:
        print(f'\n  fraud_pattern column: MISSING (no adversarial patterns in this dataset)')

    num_cols = [c for c in df.columns if c not in ['label','experience_level','fraud_pattern','embedding_shape']]
    for lbl in sorted(df['label'].unique()):
        sub = df[df['label']==lbl]
        lbl_name = 'trustworthy' if lbl == 0 else 'suspicious'
        print(f'\n  Label={lbl} ({lbl_name}) stats:')
        for c in num_cols:
            try:
                print(f'    {c}: mean={sub[c].mean():.3f}, min={sub[c].min():.3f}, max={sub[c].max():.3f}')
            except Exception:
                pass

for f in npy_labels:
    labels = np.load(f)
    vc = {int(v): int((labels==v).sum()) for v in np.unique(labels)}
    print(f'\n{f.name}: {vc}')

print('\n=== ISSUES IDENTIFIED ===')
issues = []
for f in csv_files:
    df = pd.read_csv(f)
    if 'fraud_pattern' not in df.columns:
        issues.append('No fraud_pattern column - dataset lacks adversarial examples')
    bad_feats = [feat for feat in old_feature_names if feat in df.columns]
    if bad_feats:
        issues.append(f'Old feature names present: {bad_feats} (mismatch with inference pipeline)')
    if 'label' in df.columns:
        vc = df['label'].value_counts()
        if vc.get(1,0) == 0:
            issues.append('No suspicious=1 samples (label encoding wrong or missing)')
        elif vc.get(1,0)/len(df) < 0.40:
            issues.append(f'Imbalanced: suspicious={vc.get(1,0)/len(df)*100:.1f}% (target 45-55%)')

if issues:
    for i, issue in enumerate(issues, 1):
        print(f'  {i}. {issue}')
else:
    print('  No issues found.')

print('\n=== END AUDIT ===')
