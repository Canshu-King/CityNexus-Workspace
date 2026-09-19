$file='D:\\moodle\\CityNexus\\visio\\CityNexus_Visio_Model_Baseline_v1.0.1_RC2.vsdx'
$app=New-Object -ComObject Visio.Application; $app.Visible=$false
$doc=$app.Documents.Open($file)
$uc=$doc.Pages.Item('P1_UC_Overview')
$b=$uc.Shapes.ItemFromID(1)
$b.CellsU('Width').FormulaU='10.2 in'; $b.CellsU('Height').FormulaU='6.4 in'; $b.CellsU('PinX').FormulaU='6.7 in'; $b.CellsU('PinY').FormulaU='3.75 in'
foreach($p in $doc.Pages){ foreach($s in $p.Shapes){ try { $s.CellsU('Char.Font').FormulaU='"Segoe UI"' } catch {} } }
$doc.Save(); $doc.Close(); $app.Quit()
