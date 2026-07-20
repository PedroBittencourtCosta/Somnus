import openpyxl

def dump_excel(filepath, out_file):
    out_file.write(f"\n--- {filepath} ---\n")
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active
    for row in ws.iter_rows(values_only=True):
        out_file.write(str(row) + '\n')

with open('dump_excel.txt', 'w', encoding='utf-8') as f:
    dump_excel(r'c:\Users\pedro\Documents\Somnus\Somnus_Relatorio_8 (5).xlsx', f)
    dump_excel(r'c:\Users\pedro\Documents\Somnus\Somnus_Relatorio_13 (5).xlsx', f)
