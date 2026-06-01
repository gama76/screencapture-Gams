@echo off
cd /d "%~dp0"
if exist "dist\GestionnaireScreenshots_v12\GestionnaireScreenshots_v12.exe" (
  "dist\GestionnaireScreenshots_v12\GestionnaireScreenshots_v12.exe"
) else if exist "dist\GestionnaireScreenshots_v11\GestionnaireScreenshots_v11.exe" (
  "dist\GestionnaireScreenshots_v11\GestionnaireScreenshots_v11.exe"
) else if exist "dist\GestionnaireScreenshots_v10\GestionnaireScreenshots_v10.exe" (
  "dist\GestionnaireScreenshots_v10\GestionnaireScreenshots_v10.exe"
) else if exist "dist\GestionnaireScreenshots_v9\GestionnaireScreenshots_v9.exe" (
  "dist\GestionnaireScreenshots_v9\GestionnaireScreenshots_v9.exe"
) else if exist "dist\GestionnaireScreenshots_v8\GestionnaireScreenshots_v8.exe" (
  "dist\GestionnaireScreenshots_v8\GestionnaireScreenshots_v8.exe"
) else if exist "dist\GestionnaireScreenshots_v7\GestionnaireScreenshots_v7.exe" (
  "dist\GestionnaireScreenshots_v7\GestionnaireScreenshots_v7.exe"
) else if exist "dist\GestionnaireScreenshots_v6\GestionnaireScreenshots_v6.exe" (
  "dist\GestionnaireScreenshots_v6\GestionnaireScreenshots_v6.exe"
) else if exist "dist\GestionnaireScreenshots_v5\GestionnaireScreenshots_v5.exe" (
  "dist\GestionnaireScreenshots_v5\GestionnaireScreenshots_v5.exe"
) else if exist "dist\GestionnaireScreenshots_v4\GestionnaireScreenshots_v4.exe" (
  "dist\GestionnaireScreenshots_v4\GestionnaireScreenshots_v4.exe"
) else if exist "dist\GestionnaireScreenshots_v3\GestionnaireScreenshots_v3.exe" (
  "dist\GestionnaireScreenshots_v3\GestionnaireScreenshots_v3.exe"
) else if exist "dist\GestionnaireScreenshots_v2\GestionnaireScreenshots_v2.exe" (
  "dist\GestionnaireScreenshots_v2\GestionnaireScreenshots_v2.exe"
) else (
  "dist\GestionnaireScreenshots\GestionnaireScreenshots.exe"
)
