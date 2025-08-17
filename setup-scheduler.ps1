# PowerShell script to create a Windows scheduled task for the website monitor
# Run this script as Administrator

param(
    [int]$IntervalMinutes = 30,
    [string]$TaskName = "WebpacStatusMonitor"
)

# Get the current directory
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
$NodePath = (Get-Command node).Source
$ScriptPath = Join-Path $ScriptDirectory "index.js"

Write-Host "Setting up scheduled task..." -ForegroundColor Green
Write-Host "Task Name: $TaskName" -ForegroundColor Yellow
Write-Host "Interval: Every $IntervalMinutes minutes" -ForegroundColor Yellow
Write-Host "Script Path: $ScriptPath" -ForegroundColor Yellow
Write-Host "Node Path: $NodePath" -ForegroundColor Yellow

try {
    # Create the action (what to run)
    $Action = New-ScheduledTaskAction -Execute $NodePath -Argument $ScriptPath -WorkingDirectory $ScriptDirectory

    # Create the trigger (when to run)
    $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 365)

    # Create task settings
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

    # Create the principal (run as current user)
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

    # Register the task
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force

    Write-Host "✅ Scheduled task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host "The task will run every $IntervalMinutes minutes starting now." -ForegroundColor Green
    Write-Host ""
    Write-Host "To manage the task:" -ForegroundColor Cyan
    Write-Host "• View: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "• Start: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "• Stop: Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "• Remove: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor White
    Write-Host "• Or use Task Scheduler GUI: taskschd.msc" -ForegroundColor White

} catch {
    Write-Host "❌ Error creating scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure you're running PowerShell as Administrator" -ForegroundColor Yellow
}