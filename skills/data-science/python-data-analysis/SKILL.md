---
name: python-data-analysis
description: "Data analysis, visualization, and statistics with Python — Pandas for data manipulation, Matplotlib/Seaborn for charts, and statistical analysis patterns for research/skripsi."
tags: [pandas, matplotlib, data-analysis, visualization, statistics, research]
---

# Python Data Analysis

Comprehensive guide for data manipulation, statistical analysis, and visualization using Python. Covers Pandas, Matplotlib, Seaborn, and common patterns for academic research (skripsi).

## When to Use
- User needs to analyze data (CSV, Excel, JSON)
- User wants charts/graphs for research papers or presentations
- User needs statistical summaries, frequency distributions, or correlations
- User mentions "analisis data", "grafik", "chart", "statistik", "pandas", "matplotlib"

## Quick Reference

| Task | Tool |
|------|------|
| Read/clean/transform data | Pandas |
| Statistical summaries | Pandas + NumPy |
| Bar/line/scatter/pie charts | Matplotlib |
| Heatmaps, styled plots | Seaborn |
| Academic-quality export | `dpi=300, bbox_inches='tight'` |

## Installation
```bash
pip install pandas numpy matplotlib seaborn openpyxl xlrd
```

## Pandas: Data Manipulation

### Reading Data
```python
import pandas as pd
df = pd.read_csv('data.csv')
df = pd.read_excel('data.xlsx')
df.head(); df.info(); df.describe()
```

### Cleaning
```python
df.isnull().sum()           # Check missing
df.dropna()                 # Drop missing rows
df.fillna(df.mean())        # Fill with mean
df.drop_duplicates()        # Remove duplicates
df['col'] = df['col'].astype(int)  # Type conversion
```

### Transformation
```python
# New columns
df['total'] = df['price'] * df['quantity']
df['group'] = df['age'].apply(lambda x: 'Young' if x < 30 else 'Old')

# Group by
df.groupby('city')['sales'].agg(['sum', 'mean', 'count'])

# Pivot table
pd.pivot_table(df, values='sales', index='city', columns='product', aggfunc='sum')

# Merge
pd.merge(df1, df2, on='id')
```

### For Skripsi
```python
# Questionnaire analysis pattern
df = pd.read_excel('data_kuesioner.xlsx')
df['total_score'] = df[['q1','q2','q3','q4','q5']].sum(axis=1)
df['category'] = pd.cut(df['total_score'], bins=[0,10,20,30], labels=['Low','Medium','High'])
summary = df.groupby('category').agg({'total_score': ['count','mean','std','min','max']})
summary.to_excel('hasil_analisis.xlsx')
```

## Matplotlib: Visualization

### Academic Style Setup
```python
import matplotlib.pyplot as plt
plt.style.use('seaborn-v0_8-paper')
plt.rcParams.update({'font.size': 12, 'font.family': 'serif', 'axes.labelsize': 12})
```

### Common Chart Types
```python
# Bar chart
plt.bar(categories, values, color='steelblue', edgecolor='black')
plt.savefig('chart.png', dpi=300, bbox_inches='tight')

# Line chart with markers
plt.plot(x, y, marker='o', linewidth=2, markersize=8)

# Scatter plot
plt.scatter(x, y, alpha=0.7)

# Pie chart
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)

# Histogram
plt.hist(data, bins=30, edgecolor='black')

# Box plot
plt.boxplot([data_before, data_after], labels=['Sebelum', 'Sesudah'])
```

### Comparison Chart (Pre/Post)
```python
x = np.arange(len(categories))
width = 0.35
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x - width/2, before, width, label='Sebelum', color='lightcoral')
ax.bar(x + width/2, after, width, label='Sesudah', color='lightgreen')
ax.legend()
plt.savefig('perbandingan.png', dpi=300, bbox_inches='tight')
```

### Heatmap (Seaborn)
```python
import seaborn as sns
corr = df[['var1','var2','var3']].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, square=True)
```

### Multiple Subplots
```python
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes[0,0].bar(...)
axes[0,1].plot(...)
plt.tight_layout()
```

## Export Formats
```python
plt.savefig('chart.png', dpi=300, bbox_inches='tight')  # Thesis (high DPI)
plt.savefig('chart.pdf', bbox_inches='tight')            # Vector (scalable)
df.to_excel('output.xlsx', index=False)                  # Data export
df.to_latex('table.tex', index=False)                    # LaTeX table
```

## Statistical Analysis Patterns
```python
# Descriptive
df['score'].describe()  # count, mean, std, min, 25%, 50%, 75%, max

# Frequency distribution
freq = df['category'].value_counts()
freq_pct = df['category'].value_counts(normalize=True) * 100

# Correlation
df.corr()
df['x'].corr(df['y'])

# Cross-tabulation
pd.crosstab(df['gender'], df['satisfaction'], normalize='index') * 100
```

## Pitfalls
- Use `/usr/bin/python3` on this server (Hermes venv has broken lxml)
- Always `bbox_inches='tight'` to avoid clipped labels
- For Indonesian labels, ensure UTF-8 encoding
- Large files: use `chunksize` parameter in `pd.read_csv()`
- Vectorized operations >> loops (100x faster)
