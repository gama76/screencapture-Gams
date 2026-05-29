@echo off
cd /d "%~dp0"
if exist "dist\GestionnaireScreenshots_v4\GestionnaireScreenshots_v4.exe" (
  "dist\GestionnaireScreenshots_v4\GestionnaireScreenshots_v4.exe"
) else if exist "dist\GestionnaireScreenshots_v3\GestionnaireScreenshots_v3.exe" (
  "dist\GestionnaireScreenshots_v3\GestionnaireScreenshots_v3.exe"
) else if exist "dist\GestionnaireScreenshots_v2\GestionnaireScreenshots_v2.exe" (
  "dist\GestionnaireScreenshots_v2\GestionnaireScreenshots_v2.exe"
) else (
  "dist\GestionnaireScreenshots\GestionnaireScreenshots.exe"
)
