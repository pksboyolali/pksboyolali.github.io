@echo off
rem Membuka halaman admin (/admin/) di Edge atau Chrome.
rem Sveltia CMS tidak berjalan di Firefox / Zen, jadi halaman admin sengaja
rem dibuka di peramban berbasis Chromium.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\buka.ps1" -Target admin
echo.
pause
