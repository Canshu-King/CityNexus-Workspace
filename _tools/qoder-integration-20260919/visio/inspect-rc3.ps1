$file='D:\\moodle\\CityNexus\\visio\\CityNexus_Visio_Model_Baseline_v1.0.2_RC3.vsdx'; $app=New-Object -ComObject Visio.Application; $app.Visible=$false; $doc=$app.Documents.Open($file)
foreach($p in $doc.Pages){ Write-Output ("PAGE {0} shapes={1} width={2} height={3}" -f $p.Name,$p.Shapes.Count,$p.PageSheet.CellsU('PageWidth').ResultIU,$p.PageSheet.CellsU('PageHeight').ResultIU); foreach($s in $p.Shapes){try{$v=$s.CellsU('Prop.SpecId').FormulaU; if($v){Write-Output ("SPEC {0} {1}" -f $s.ID,$v)}}catch{}} }
$doc.Close();$app.Quit()
