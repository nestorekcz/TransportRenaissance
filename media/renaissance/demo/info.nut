/* Transport Renaissance demonstration. GPL-2.0-only. */
class RenaissanceDemoInfo extends GSInfo {
    function GetAuthor() { return "Transport Renaissance contributors"; }
    function GetName() { return "Renaissance Coast"; }
    function GetShortName() { return "TRDC"; }
    function GetDescription() { return "Builds a reproducible coastal freight railway for the independent Transport Renaissance fork."; }
    function GetVersion() { return 1; }
    function GetDate() { return "2026-11-01"; }
    function GetAPIVersion() { return "15"; }
    function CreateInstance() { return "RenaissanceDemo"; }
}
RegisterGS(RenaissanceDemoInfo());
