# Create a temporary directory for packaging
New-Item -ItemType Directory -Force -Path .\deployment_package | Out-Null
Set-Location .\deployment_package

# Install dependencies into the deployment package directory
pipenv run pip install --no-deps -t . discord.py anthropic boto3

# Create src directory in the deployment package
New-Item -ItemType Directory -Force -Path .\src | Out-Null

# Function to copy a file if it exists
function Copy-FileIfExists {
    param (
        [string]$SourceFile,
        [string]$DestinationFile = $SourceFile
    )
    if (Test-Path ..\src\$SourceFile) {
        Copy-Item ..\src\$SourceFile .\src\$DestinationFile
        Write-Output "Copied $SourceFile to the package."
    } else {
        Write-Warning "$SourceFile not found in the src directory. Make sure this file is in the correct location."
    }
}

# Copy Lambda function files
Copy-FileIfExists "main.py"
Copy-FileIfExists "settings.py"

# Create the deployment package
Compress-Archive -Path * -DestinationPath ..\deployment_package.zip -Force

# Clean up
Set-Location ..
Remove-Item -Recurse -Force .\deployment_package

Write-Output "Deployment package created: deployment_package.zip"

# Final check
if (Test-Path .\deployment_package.zip) {
    Write-Output "Package created successfully."
} else {
    Write-Error "Failed to create deployment package."
}
