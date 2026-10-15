; Fleet Tauri: kill UI + backend before install/uninstall (backend locks resources/*.exe).
; Client registration: mcp-clients.nsh (vendored fleet canonical) registers the
; stdio backend in detected AI tools (Claude/Cursor/Antigravity/OpenCode).
!define MCP_REG_NAME "reversing-mcp"
!define MCP_REG_EXE "reversing-mcp-backend.exe"
!include "${__FILEDIR__}\mcp-clients.nsh"

!macro KillProcesses
  DetailPrint "Stopping processes..."
  ExecWait 'taskkill /F /IM "reversing-mcp-backend.exe" /T' $0
  ExecWait 'taskkill /F /IM "reversing-mcp-native.exe" /T' $0
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  !insertmacro McpClientsRegister
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillProcesses
  !insertmacro McpClientsUnregister
!macroend
