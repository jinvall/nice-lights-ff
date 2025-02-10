import sqlite3

# Paths to the old and new database files
old_db_paths = [
    r"C:\Users\jason\tracking_logger_v1.1\tracking_data.db",
    r"C:\Users\jason\tracking_logger_v1.0\tracking_data.db",
    r"C:\Users\jason\tracking_logger_v0.1\tracking_data.db"
]
new_db_path = r"tracking_data.db"

# Connect to the new database
new_conn = sqlite3.connect(new_db_path)
new_cursor = new_conn.cursor()

# Function to migrate data from an old database
def migrate_data(old_db_path):
    old_conn = sqlite3.connect(old_db_path)
    old_cursor = old_conn.cursor()
    
    # Fetch data from the old database
    old_cursor.execute('SELECT timestamp, identifier, rssi, distance, uid, data_type, occurrences FROM tracking_data')
    rows = old_cursor.fetchall()

    # Insert data into the new database
    for row in rows:
        new_cursor.execute('''
            INSERT INTO tracking_data (timestamp, identifier, rssi, distance, uid, data_type, occurrences)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', row)

    # Commit and close the old connection
    new_conn.commit()
    old_conn.close()

# Migrate data from all old databases
for old_db_path in old_db_paths:
    migrate_data(old_db_path)

# Close the new connection
new_conn.close()

print("Data migration completed successfully!")
