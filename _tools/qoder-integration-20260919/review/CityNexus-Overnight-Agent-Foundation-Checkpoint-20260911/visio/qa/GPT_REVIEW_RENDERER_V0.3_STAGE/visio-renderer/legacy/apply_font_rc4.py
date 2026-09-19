import win32com.client
f=r'D:\\moodle\\CityNexus\\visio\\CityNexus_Visio_Model_Baseline_v1.0.3_RC4.vsdx'; a=win32com.client.Dispatch('Visio.Application'); a.Visible=False; a.AlertResponse=7; d=a.Documents.OpenEx(f,64); fid=next(i for i in range(1,d.Fonts.Count+1) if d.Fonts.Item(i).Name=='Segoe UI')
for p in d.Pages:
    p.PageSheet.CellsU('FillForegnd').FormulaU='RGB(248,250,252)'
    for s in p.Shapes:
        try:s.CellsU('Char.Font').FormulaU=str(fid)
        except:pass
d.Save(); d.Close(); a.Quit(); print(fid)
