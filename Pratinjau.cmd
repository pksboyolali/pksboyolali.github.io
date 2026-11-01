@echo off
setlocal enabledelayedexpansion
title Pratinjau Situs DPD PKS Boyolali
cd /d "%~dp0"

rem ==== Mode: tambahkan kata "draf" saat menjalankan untuk ikut menampilkan artikel draf ====
set "DRAF="
if /i "%~1"=="draf" set "DRAF=--buildDrafts"

rem ==== Cari Hugo: folder _tools -> PATH -> Downloads\Compressed ====
set "HUGO="
if exist "%~dp0_tools\hugo.exe" set "HUGO=%~dp0_tools\hugo.exe"
if not defined HUGO for %%I in (hugo.exe) do if not "%%~$PATH:I"=="" set "HUGO=%%~$PATH:I"
if not defined HUGO if exist "%USERPROFILE%\Downloads\Compressed\hugo.exe" set "HUGO=%USERPROFILE%\Downloads\Compressed\hugo.exe"

if not defined HUGO (
  echo.
  echo  Hugo tidak ditemukan.
  echo.
  echo  Unduh "hugo extended" untuk Windows di:
  echo    https://github.com/gohugoio/hugo/releases
  echo  lalu taruh hugo.exe ke folder _tools di samping file ini.
  echo.
  pause
  exit /b 1
)

echo.
echo   Situs  : http://localhost:1313
echo   Admin  : http://localhost:1313/admin/
if defined DRAF (echo   Mode   : ikut menampilkan artikel DRAF) else (echo   Mode   : hanya artikel terbit)
echo   Hugo   : %HUGO%
echo.
echo   Tutup jendela ini atau tekan Ctrl+C untuk mematikan server.
echo.

if not "%PRATINJAU_NO_BROWSER%"=="1" (
  rem Situs dibuka di peramban bawaan, admin sengaja di Edge/Chrome
  rem karena Sveltia CMS tidak berjalan di Firefox / Zen.
  start "" powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0scripts\buka.ps1" -Target semua
)

"%HUGO%" server --port 1313 --bind 127.0.0.1 --disableFastRender %DRAF%

echo.
echo Server berhenti.
pause
