import os
import logging
import datetime
import time
import serial
import sqlite3

# Ensure directory exists
log_dir = 'tracking_logger'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Ensure log file exists
log_file = os.path.join(log_dir, 'tracking_debug.log')
if not os.path.exists(log_file):
    open(log_file, 'w').close()

# Configure logging
logging.basicConfig(level=logging.DEBUG, handlers=[
    logging.FileHandler(log_file),
    logging.StreamHandler()
])

logging.debug("Starting tracker script...")

# Configure the serial port
try:
    ser = serial.Serial('COM31', 115200, timeout=1)  # Adjust baud rate if necessary
    logging.debug("Serial port configured.")
except serial.SerialException as e:
    logging.error(f"Failed to configure serial port: {e}")
    exit()

# Connect to SQLite database
DATABASE = 'tracking_data.db'
db_path = os.path.join(os.path.dirname(__file__), DATABASE)
conn = sqlite3.connect(db_path)
logging.debug("Connected to SQLite database.")

def track_signals():
    while True:
        try:
            logging.debug("Reading line from serial port...")
            line = ser.readline().decode('utf-8').strip()
            logging.debug(f"Received line: '{line}'")

            if line:
                # Check for lines that do not match the expected format
                if 'networks found' in line or 'Scanning for networks' in line or 'No networks found' in line:
                    logging.warning(f"Non-data line received and skipped: {line}")
                    continue  # Skip this line

                # Process the data line
                if 'Hidden' in line:
                    parts = line.split(',')
                    if len(parts) == 4:
                        ssid = parts[0].replace('SSID: ', '').strip()
                        rssi = int(parts[1].replace('RSSI: ', '').strip())
                        mac = parts[2].replace('MAC: ', '').strip()
                        hidden = parts[3].replace('Hidden: ', '').strip()

                        # Determine if the SSID is scanning (replace this with your actual logic)
                        is_scanning = hidden == 'Yes'

                        log_entry = {
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "SSID": ssid if ssid != "Hidden" else "Hidden",
                            "RSSI": rssi,
                            "MAC": mac,
                            "is_scanning": is_scanning
                        }
                        logging.debug(f"Parsed data: {log_entry}")

                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO tracking_data (timestamp, identifier, rssi, distance, uid, data_type, occurrences, is_scanning)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (int(time.time()), log_entry["SSID"], log_entry["RSSI"], 0, log_entry["MAC"], 'Dynamic', 1, log_entry["is_scanning"]))
                        conn.commit()
                        logging.debug("Data inserted into database.")
                    else:
                        logging.warning(f"Incomplete data received: {parts}")
                else:
                    logging.warning(f"Unexpected line format received: {line}")
            else:
                logging.debug("Empty line received.")
        except Exception as e:
            logging.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    track_signals()
