import win32com.client
f=r'D:\\moodle\\CityNexus\\visio\\CityNexus_Visio_Model_Baseline_v1.0.3_RC4.vsdx'; a=win32com.client.Dispatch('Visio.Application'); a.Visible=False; a.AlertResponse=7; d=a.Documents.OpenEx(f,64)
def walk(coll,color,line):
    for s in coll:
        try:
            s.CellsU('FillForegnd').FormulaU='RGB(%d,%d,%d)'%color; s.CellsU('LineColor').FormulaU='RGB(%d,%d,%d)'%line
        except: pass
        try: walk(s.Shapes,color,line)
        except: pass
for p in d.Pages:
    for s in p.Shapes:
        n=s.Name.lower()
        if '参与者' in n or 'actor' in n: walk([s],(219,234,254),(37,99,235))
        elif '用例' in n or 'use case' in n: walk([s],(237,233,254),(124,58,237))
        elif '类' in n or 'class' in n: walk([s],(204,251,241),(15,118,110))
        elif '关联' in n or 'composition' in n or 'dependency' in n or '扩展' in n: walk([s],(209,250,229),(5,150,105))
d.Save(); d.Close(); a.Quit(); print('palette applied')
