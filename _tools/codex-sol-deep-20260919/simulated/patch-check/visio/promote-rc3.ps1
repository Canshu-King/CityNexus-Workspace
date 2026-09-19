$file='D:\\moodle\\CityNexus\\visio\\CityNexus_Visio_Model_Baseline_v1.0.2_RC3.vsdx'
$app=New-Object -ComObject Visio.Application; $app.Visible=$false
$doc=$app.Documents.Open($file)
$visSectionProp=243; $visTagDefault=0
function Set-SpecId($shape,$id){ try { if(-not $shape.CellExistsU('Prop.SpecId',0)){ $shape.AddNamedRow($visSectionProp,'SpecId',$visTagDefault) | Out-Null }; $shape.CellsU('Prop.SpecId').FormulaU='"'+$id+'"' } catch {} }
foreach($p in $doc.Pages){ $p.PageSheet.CellsU('FillForegnd').FormulaU='RGB(248,250,252)'; foreach($s in $p.Shapes){ try{$s.CellsU('Char.Font').FormulaU='FONT("Segoe UI")'}catch{} } }
$uc=$doc.Pages.Item('P1_UC_Overview')
$map=@{1='BOUNDARY';6='ACT-TRAVELER';12='ACT-CITY-DATA';13='ACT-MOBILITY';14='ACT-BOOKING';15='ACT-PAYAUTH';16='ACT-CONTEXT';17='UC-02';18='UC-04';19='UC-05';20='UC-06';21='UC-07';22='UC-11';23='UC-08';24='UC-09';25='UC-10';26='UC-12'}
foreach($kv in $map.GetEnumerator()){Set-SpecId $uc.Shapes.ItemFromID([int]$kv.Key) $kv.Value}
$dom=$doc.Pages.Item('P1_Domain_Overview'); $dmap=@{1='Traveler';6='Journey';11='JourneyTwin';16='Commitment';21='PlanVersion';26='Event';31='Constraint';36='Activity';41='ReplanProposal';46='Place';51='CityService'}; foreach($kv in $dmap.GetEnumerator()){Set-SpecId $dom.Shapes.ItemFromID([int]$kv.Key) $kv.Value}
$sty=$doc.Pages.Item('00_Style_Guide'); $smap=@{1='ACTOR_HUMAN';2='ACTOR_EXTERNAL';3='UC-10';4='Journey';9='JourneyTwin';14='ScoreBreakdown'}; foreach($kv in $smap.GetEnumerator()){Set-SpecId $sty.Shapes.ItemFromID([int]$kv.Key) $kv.Value}
function Add-Header($page,$text,$x1,$y1,$x2,$y2){$sh=$page.DrawRectangle($x1,$y1,$x2,$y2);$sh.Text=$text;try{$sh.CellsU('FillForegnd').FormulaU='RGB(248,250,252)';$sh.CellsU('LinePattern').FormulaU='0';$sh.CellsU('Char.Font').FormulaU='FONT("Segoe UI")';$sh.CellsU('Char.Size').FormulaU='10 pt'}catch{}}
Add-Header $sty 'CityNexus — Style Guide`nProposed Model Baseline v1.0.2 RC3`nPART 1 • SIMPLIFIED' 0.2 7.65 11.5 8.15
Add-Header $uc 'CityNexus — Core Use Case Overview`nSmart City Traveler System • Proposed Model Baseline v1.0.2`nPART 1 • SIMPLIFIED' 0.2 7.05 13.1 7.45
Add-Header $dom 'CityNexus — Core Domain Overview`nSmart City Traveler System • Proposed Model Baseline v1.0.2`nPART 1 • SIMPLIFIED' 0.2 6.95 13.1 7.35
$doc.Save();$doc.Close();$app.Quit()
