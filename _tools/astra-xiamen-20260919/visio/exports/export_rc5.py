import win32com.client
import os
import time

# 等 2 秒让 Visio 进程完全释放
time.sleep(2)

visio = win32com.client.Dispatch('Visio.Application')
visio.Visible = False

# 打开 RC5
vsdx_path = r'D:\moodle\CityNexus\visio\CityNexus_Visio_Model_Baseline_v1.0.4_RC5.vsdx'
doc = visio.Documents.Open(vsdx_path)

# 导出 PDF
export_dir = r'D:\moodle\CityNexus\visio\exports'
os.makedirs(export_dir, exist_ok=True)
pdf_path = os.path.join(export_dir, 'CityNexus_Visio_Model_Baseline_v1.0.4_RC5.pdf')

# ExportAsFixedFormat 签名：
# ExportAsFixedFormat(Format, OutputFileName, OutputQuality, DeleteDocAfterExport, DataOnly, DocProperties, LoadVBA, CreateExternalHyperlinkFile)
doc.ExportAsFixedFormat(
    1,  # Format = visioPDF
    pdf_path,  # OutputFileName
    1,  # OutputQuality = visioExprtQualityDocStandard
    0,  # DeleteDocAfterExport
    0,  # DataOnly
    0,  # DocProperties
    0,  # LoadVBA
    0  # CreateExternalHyperlinkFile
)

print(f'✅ PDF 已导出：{pdf_path}')
print(f'   页数：{doc.Pages.Count} 页')
for i, page in enumerate(doc.Pages):
    print(f'   - Page {i+1}: {page.Name} ({page.Shapes.Count} 个形状)')

doc.Close()
visio.Quit()
