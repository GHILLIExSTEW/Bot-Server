@echo off
echo Stopping master service manager...
python master_service_manager.py stop
timeout /t 5
echo Starting master service manager...
python master_service_manager.py start
echo Services restarted!
pause
