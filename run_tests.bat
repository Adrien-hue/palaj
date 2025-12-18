@echo off
echo =============================
echo   Lancement des tests Pytest
echo =============================

REM Exécution des tests avec mesure de couverture
pytest --cov=core --cov-report=html --maxfail=1 -v

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR - Certains tests ont echoue ou la couverture est insuffisante.
    echo Consultez le rapport HTML pour plus de details.
) ELSE (
    echo.
    echo SUCCESS - Tous les tests ont reussi !
)

REM Ouvrir le rapport de couverture dans le navigateur
IF EXIST htmlcov\index.html (
    start htmlcov\index.html
)

pause
