# Per-repo fleet start config for reversing-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'reversing-mcp'
    BackendPort  = 10750
    FrontendPort = 10751
    HealthPath   = '/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'reversing_mcp.server:app'
        WorkDir       = '.'
        PythonPath    = 'src'
        SyncExtras    = @('dev', 'clicker')
        SyncOnStart  = $true
        Env           = @{ WEB_PORT = '10750' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
