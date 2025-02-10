@echo off
echo Migrating data...
python migrate_data.py

echo Training model...
python train_model.py

echo Starting tracker...
start python tracker.py

echo Starting Flask app...
python app.py

pause
