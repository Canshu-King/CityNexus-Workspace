$file='D:\\moodle\\CityNexus\\visio\\CityNexus_Visio_Model_Baseline_v1.0.2_RC3.vsdx'; $out='D:\\moodle\\CityNexus\\visio\\exports\\phase1-rc3'; New-Item -ItemType Directory -Force -Path $out | Out-Null
$app=New-Object -ComObject Visio.Application; $app.Visible=$false; $app.AlertResponse=7; $doc=$app.Documents.OpenEx($file,64)
foreach($name in @('00_Style_Guide','P1_UC_Overview','P1_Domain_Overview')){ $p=$doc.Pages.Item($name); $safe=$name -replace '[^A-Za-z0-9_-]','_'; $p.Export((Join-Path $out ($safe+'_v1.0.2-RC3.svg'))) }
$doc.Close();$app.Quit()
