# XLSX Statistical Analysis Template (Paired T-Test)

## Multi-Sheet Layout for Research Data

Used for: Data Latih BDC PRISMA, research data export from skripsi.

### Sheet Structure (5 sheets)

| Sheet | Content |
|-------|---------|
| 1. Data Individu | Per-responden data with formulas |
| 2. Statistik Deskriptif | Mean, Median, SD, Min, Max |
| 3. Per Indikator | Aggregated by indicator |
| 4. Persentase Peningkatan | Gain score + percentage + category |
| 5. Uji Statistik | T-test results + Excel formulas |

### Styling Pattern

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

header_font = Font(bold=True, size=11, color="FFFFFF")
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
center = Alignment(horizontal='center', vertical='center', wrap_text=True)

def style_header(ws, row, cols):
    for c in range(1, cols+1):
        cell = ws.cell(row=row, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = thin_border
```

### Key Excel Formulas

```python
# Gain Score (column E = post - pre)
ws.cell(row=r, column=5).value = f"=D{r}-C{r}"

# Percentage improvement
ws.cell(row=r, column=6).value = f"=E{r}/C{r}*100"

# Summary statistics
ws.cell(row=36, column=3).value = "=AVERAGE(C5:C34)"
ws.cell(row=37, column=3).value = "=STDEV(C5:C34)"

# Paired T-Test p-value: =T.TEST(range_pre, range_post, 2, 1)
# t-hitung: =AVERAGE(E5:E34)/(STDEV(E5:E34)/SQRT(30))
```

### Pitfall: openpyxl Installation

Check and install before use:
```bash
python3 -c "import openpyxl" 2>/dev/null || pip3 install openpyxl
```

If using venv: `~/.hermes/hermes-agent/.venv/bin/pip install openpyxl`
Or use `execute_code` which resolves the correct Python environment automatically.
