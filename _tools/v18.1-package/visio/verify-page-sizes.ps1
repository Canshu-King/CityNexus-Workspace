$file = 'D:\\moodle\\CityNexus\\visio\\RC2_snapshot.vsdx'
$app = New-Object -ComObject Visio.Application
$app.Visible = $false
$doc = $app.Documents.Open($file)
for($i=1;$i -le $doc.Pages.Count;$i++) {
  $p=$doc.Pages.Item($i)
  $w=$p.PageSheet.CellsU('PageWidth').ResultIU
  $h=$p.PageSheet.CellsU('PageHeight').ResultIU
  Write-Output ("{0}: {1} x {2} in" -f $p.Name,$w,$h)
}
$doc.Close(); $app.Quit()
