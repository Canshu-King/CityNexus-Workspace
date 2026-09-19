$file = 'D:\\moodle\\CityNexus\\visio\\CityNexus_Visio_Model_Baseline_v1.0.1_RC2.vsdx'
$app = New-Object -ComObject Visio.Application
$app.Visible = $false
$doc = $app.Documents.Open($file)
$sizes = @(
  @([double]11.6929133858,[double]8.2677165354),
  @([double]13.3346456693,[double]7.5),
  @([double]13.3346456693,[double]7.5)
)
for($i=1;$i -le 3;$i++){ $p=$doc.Pages.Item($i); $p.PageSheet.CellsU('PageWidth').FormulaU = $sizes[$i-1][0]; $p.PageSheet.CellsU('PageHeight').FormulaU = $sizes[$i-1][1] }
$doc.Save(); $doc.Close(); $app.Quit()
