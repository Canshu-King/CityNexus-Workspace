import os,win32com.client
root=r'D:\\moodle\\CityNexus'; file=os.path.join(root,'visio','CityNexus_Visio_Model_Baseline_v1.0.3_RC4.vsdx'); out=os.path.join(root,'visio','exports','phase1-rc4'); os.makedirs(out,exist_ok=True)
app=win32com.client.Dispatch('Visio.Application'); app.Visible=False; app.AlertResponse=7; doc=app.Documents.OpenEx(file,64)
for n in ('00_Style_Guide','P1_UC_Overview','P1_Domain_Overview'):
    p=doc.Pages.Item(n); p.Export(os.path.join(out,n+'_v1.0.3-RC4.svg'))
doc.Close(); app.Quit()
