# DCOIR PowerShell analyzer policy for issue #262.
# DCOIR_POLICY_ID: dcoir-powershell-analyzer-policy-v1
# DCOIR_POLICY_SCOPE: collector, harness, maintained operator tooling, and maintained validation tooling from powershell_surface_inventory.json.
# DCOIR_EXCLUSIONS: none. Workflow-embedded snippets and fixture/reference files remain inventoried by #261 and are intentionally not direct analyzer targets in this child.
# DCOIR_NO_BLANKET_SUPPRESSION: This policy must not use wildcard rule exclusions, blanket generated-file ignores, or broad severity disablement.
@{
    Severity = @(
        'Error'
        'Warning'
    )

    IncludeRules = @(
        'PSAvoidUsingPlainTextForPassword'
        'PSAvoidUsingConvertToSecureStringWithPlainText'
        'PSAvoidUsingInvokeExpression'
        'PSAvoidUsingWriteHost'
        'PSUseDeclaredVarsMoreThanAssignments'
        'PSUseShouldProcessForStateChangingFunctions'
    )

    Rules = @{
        PSAvoidUsingPlainTextForPassword = @{}
        PSAvoidUsingConvertToSecureStringWithPlainText = @{}
        PSAvoidUsingInvokeExpression = @{}
        PSAvoidUsingWriteHost = @{}
        PSUseDeclaredVarsMoreThanAssignments = @{}
        PSUseShouldProcessForStateChangingFunctions = @{}
    }
}
