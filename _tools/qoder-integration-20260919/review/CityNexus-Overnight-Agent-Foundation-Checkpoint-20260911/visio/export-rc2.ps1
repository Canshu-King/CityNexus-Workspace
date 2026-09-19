$file='D:\\moodle\\CityNexus\\visio\\CityNexus_Visio_Model_Baseline_v1.0.1_RC2.vsdx'; $out='D:\\moodle\\CityNexus\\visio\\exports\\phase1-rc2'; New-Item -ItemType Directory -Force -Path $out | Out-Null
$app=New-Object -ComObject Visio.Application; $app.Visible=$false; $doc=$app.Documents.Open($file)
foreach($name in @('00_Style_Guide','P1_UC_Overview','P1_Domain_Overview')){ $p=$doc.Pages.Item($name); $safe=$name -replace '[^A-Za-z0-9_-]','_'; $p.Export((Join-Path $out ($safe+'_v1.0.1-RC2.svg'))) }
$doc.Close();$app.Quit()
