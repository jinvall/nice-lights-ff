#!/bin/bash

# Step 1: Migrate Data
echo "Migrating data..."
python3 migrate_data.py

# Step 2: Train Model
echo "Training model..."
python3 train_model.py

# Step 3: Start Tracker
echo "Starting tracker..."
python3 tracker.py &

# Step 4: Start Flask App
echo "Starting Flask app..."
python3 app.py
