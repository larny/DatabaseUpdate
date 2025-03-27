@echo off
call activate base
python run_app.py --server.enableXsrfProtection=false
pause