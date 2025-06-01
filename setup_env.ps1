# PowerShell script to set up environment variables
# Run this script with administrator privileges

# Generate secure random values for keys
$secretKey = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
$securitySalt = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

# Set environment variables for the current user
[System.Environment]::SetEnvironmentVariable('SECRET_KEY', $secretKey, 'User')
[System.Environment]::SetEnvironmentVariable('SECURITY_PASSWORD_SALT', $securitySalt, 'User')
[System.Environment]::SetEnvironmentVariable('LOG_LEVEL', 'INFO', 'User')
[System.Environment]::SetEnvironmentVariable('CACHE_TYPE', 'simple', 'User')
[System.Environment]::SetEnvironmentVariable('RATELIMIT_STORAGE_URL', 'memory://', 'User')

# Optional: Set these if you have the values
# [System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'your-openai-api-key', 'User')
# [System.Environment]::SetEnvironmentVariable('GOOGLE_API_KEY', 'your-google-api-key', 'User')
# [System.Environment]::SetEnvironmentVariable('MICROSOFT_API_KEY', 'your-microsoft-api-key', 'User')

Write-Host "Environment variables have been set successfully!"
Write-Host "SECRET_KEY: $secretKey"
Write-Host "SECURITY_PASSWORD_SALT: $securitySalt"
Write-Host "LOG_LEVEL: INFO"
Write-Host "CACHE_TYPE: simple"
Write-Host "RATELIMIT_STORAGE_URL: memory://"

# Instructions for the user
Write-Host "`nTo apply these changes to your current session, please restart your PowerShell window."
Write-Host "To verify the settings, run: Get-ChildItem env: | Where-Object { `$_.Name -match 'SECRET_KEY|SECURITY_PASSWORD_SALT|LOG_LEVEL|CACHE_TYPE|RATELIMIT_STORAGE_URL' }" 