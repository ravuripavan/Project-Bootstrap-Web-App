@echo off
REM Test runner script for Project Bootstrap Backend (Windows)

echo Project Bootstrap Backend - Test Runner
echo.

REM Set test database URL
set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bootstrap_test

REM Check for command argument
if "%1"=="" goto all
if "%1"=="all" goto all
if "%1"=="projects" goto projects
if "%1"=="coverage" goto coverage
if "%1"=="fast" goto fast
goto unknown

:all
echo Running all tests...
echo.
pytest tests\ -v
goto end

:projects
echo Running project API tests...
echo.
pytest tests\test_api_projects.py -v
goto end

:coverage
echo Running tests with coverage...
echo.
pytest tests\ --cov=app --cov-report=term-missing --cov-report=html
echo.
echo Coverage report generated in htmlcov\index.html
goto end

:fast
echo Running fast tests only...
echo.
pytest tests\ -v -m "not slow"
goto end

:unknown
echo Unknown option: %1
echo Usage: run_tests.bat [all^|projects^|coverage^|fast]
exit /b 1

:end
echo.
echo Tests completed!
