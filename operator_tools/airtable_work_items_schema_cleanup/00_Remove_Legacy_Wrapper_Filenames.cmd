@echo off
setlocal
cd /d "%~dp0"
echo This removes old long wrapper filenames from this tool folder.
echo New numbered wrappers remain in place.
echo.
if exist "Run_DCOIR_WorkItemsSchemaCleanup_ApplyOptions.cmd" del /f /q "Run_DCOIR_WorkItemsSchemaCleanup_ApplyOptions.cmd"
if exist "Run_DCOIR_WorkItemsSchemaCleanup_ApplySafe.cmd" del /f /q "Run_DCOIR_WorkItemsSchemaCleanup_ApplySafe.cmd"
if exist "Run_DCOIR_WorkItemsSchemaCleanup_AttemptApiOptionDelete_DANGEROUS.cmd" del /f /q "Run_DCOIR_WorkItemsSchemaCleanup_AttemptApiOptionDelete_DANGEROUS.cmd"
if exist "Run_DCOIR_WorkItemsSchemaCleanup_AttemptFieldDelete_DANGEROUS.cmd" del /f /q "Run_DCOIR_WorkItemsSchemaCleanup_AttemptFieldDelete_DANGEROUS.cmd"
if exist "Run_DCOIR_WorkItemsSchemaCleanup_DryRun.cmd" del /f /q "Run_DCOIR_WorkItemsSchemaCleanup_DryRun.cmd"
if exist "Run_DCOIR_WorkItemsSchemaCleanup_GenerateOptionDeleteScript.cmd" del /f /q "Run_DCOIR_WorkItemsSchemaCleanup_GenerateOptionDeleteScript.cmd"
if exist "Run_DCOIR_WorkItemsSchemaCleanup_SelfTest.cmd" del /f /q "Run_DCOIR_WorkItemsSchemaCleanup_SelfTest.cmd"
if exist "Run_DCOIR_WorkItemsSchemaCleanup_Verify.cmd" del /f /q "Run_DCOIR_WorkItemsSchemaCleanup_Verify.cmd"
echo Legacy wrapper cleanup complete.
echo GitHub Desktop should show deletions for old wrapper files if they existed.
echo.
pause
