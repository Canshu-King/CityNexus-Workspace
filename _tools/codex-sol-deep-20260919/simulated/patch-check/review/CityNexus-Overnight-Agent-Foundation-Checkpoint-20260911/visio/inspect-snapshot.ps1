$file='D:\\moodle\\CityNexus\\visio\\CityNexus_Visio_Model_Baseline_v1.0.1_RC2.vsdx'; $app=New-Object -ComObject Visio.Application; $app.Visible=$false; $doc=$app.Documents.Open($file)
foreach($p in $doc.Pages){ Write-Output ("{0}: {1} shapes" -f $p.Name,$p.Shapes.Count) }
$doc.Close();$app.Quit()
