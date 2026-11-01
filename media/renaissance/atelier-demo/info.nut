/* Original approval fixture; GPL-2.0-only. */
class AtelierInfo extends GSInfo {
    function GetAuthor() { return "Transport Renaissance contributors"; }
    function GetName() { return "Renaissance Atelier"; }
    function GetShortName() { return "TRAT"; }
    function GetDescription() { return "Reproducible miniature-world art approval district."; }
    function GetVersion() { return 1; }
    function GetDate() { return "2026-11-01"; }
    function GetAPIVersion() { return "15"; }
    function CreateInstance() { return "AtelierDemo"; }
}
RegisterGS(AtelierInfo());
