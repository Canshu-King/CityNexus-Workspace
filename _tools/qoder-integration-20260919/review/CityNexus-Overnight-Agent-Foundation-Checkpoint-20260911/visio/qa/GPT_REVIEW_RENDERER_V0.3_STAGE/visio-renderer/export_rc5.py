import os,win32com.client
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
f=os.path.join(root,'visio','CityNexus_Visio_Model_Baseline_v1.0.4_RC5.vsdx')
out=os.path.join(root,'visio','exports','phase1-rc5'); os.makedirs(out,exist_ok=True)
a=win32com.client.Dispatch('Visio.Application'); a.Visible=False; a.AlertResponse=7; d=a.Documents.OpenEx(f,64)
for n in ('00_Style_Guide','P1_UC_Overview','P1_Domain_Overview'):
    p=d.Pages.Item(n); p.Export(os.path.join(out,n+'_v1.0.4-RC5.svg')); p.Export(os.path.join(out,n+'_v1.0.4-RC5.png'))
d.Close(); a.Quit()
