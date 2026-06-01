@{
    # install.ps1 is an INTERACTIVE installer: its entire job is colored,
    # human-facing console output (the Say/Hdr/Ok/Warn/Die helpers). Write-Host
    # is the correct tool for that — the output is never meant to be captured,
    # piped, or redirected. PSAvoidUsingWriteHost targets library/pipeline code,
    # so it is a false positive here and is excluded by design.
    ExcludeRules = @(
        'PSAvoidUsingWriteHost'
    )
}
