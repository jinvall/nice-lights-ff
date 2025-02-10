from flask import Flask, render_template, send_from_directory, g, request, redirect, url_for, jsonify, flash
import sqlite3
import joblib
import os
from datetime import datetime
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'tracking_data.db'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    pass

# Load user callback
@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

# Load the trained models
logging.debug("Loading trained models...")
scaler = joblib.load('models/scaler.pkl')
kmeans = joblib.load('models/kmeans_model.pkl')
logging.debug("Trained models loaded successfully.")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db_path = os.path.join(app.root_path, DATABASE)
        db = g._database = sqlite3.connect(db_path)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        # Try to convert the value to an integer timestamp
        dt = datetime.fromtimestamp(int(value))
    except ValueError:
        # If it fails, assume it's a string timestamp and parse it
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return dt.strftime('%Y-%m-%d %H:%M:%S')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Insert user into the database (add your database logic here)
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        db.commit()
        flash('Registered successfully.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check user credentials (add your database logic here)
        db = get_db()
        cursor = db.cursor()
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            user = User()
            user.id = username
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cursor = db.cursor()
    # Exclude sample data (assuming 'sample' keyword is used to identify samples)
    recent_hits_data = cursor.execute('''
        SELECT * FROM tracking_data
        WHERE identifier NOT LIKE '%sample%'
        ORDER BY timestamp DESC
        LIMIT 10
    ''').fetchall()
    
    recent_hits = []
    for row in recent_hits_data:
        recent_hits.append({
            'id': row[0],
            'timestamp': row[1],
            'identifier': row[2],
            'rssi': row[3],
            'distance': row[4],
            'uid': row[5],
            'data_type': row[6],
            'occurrences': row[7],
            'is_scanning': row[8]
        })
    return render_template('dashboard.html', recent_hits=recent_hits)

@app.route('/convoys')
@login_required
def convoys():
    db = get_db()
    cursor = db.cursor()
    # Fetch convoy data (dynamic SSIDs/BSSIDs)
    convoy_data = cursor.execute('''
        SELECT timestamp, identifier, rssi, distance, uid, COUNT(*)
        FROM tracking_data
        WHERE data_type != "Static"
        GROUP BY identifier, uid
        ORDER BY timestamp DESC
    ''').fetchall()
    return render_template('convoys.html', convoy_data=convoy_data)

@app.route('/hits')
@login_required
def hits():
    db = get_db()
    cursor = db.cursor()
    # Fetch all non-static hits data (dynamic SSIDs/BSSIDs)
    hits_data = cursor.execute('''
        SELECT timestamp, identifier, rssi, distance, uid, COUNT(*)
        FROM tracking_data
        WHERE data_type != "Static"
        GROUP BY identifier, uid
        ORDER BY timestamp DESC
    ''').fetchall()
    return render_template('hits.html', hits_data=hits_data)

@app.route('/details/<uid>')
@login_required
def details(uid):
    db = get_db()
    cursor = db.cursor()
    details_data = cursor.execute('''
        SELECT timestamp, identifier, rssi, distance, occurrences, uid, is_scanning
        FROM tracking_data
        WHERE uid = ?
        ORDER BY timestamp DESC
    ''', (uid,)).fetchall()
    return render_template('details.html', details_data=details_data, uid=uid)

@app.route('/save_note', methods=['POST'])
@login_required
def save_note():
    note = request.form['note']
    uid = request.form['uid']
    # Sanitize the filename by replacing invalid characters
    sanitized_uid = uid.replace(":", "_")
    note_file = f'notes_{sanitized_uid}.txt'
    with open(note_file, 'a') as f:
        f.write(note + '\n')
    return redirect(url_for('details', uid=uid))

@app.route('/train_model')
@login_required
def train_model():
    db = get_db()
    cursor = db.cursor()
    # Fetch data for training
    data = cursor.execute('SELECT * FROM tracking_data').fetchall()
    df = pd.DataFrame(data, columns=['id', 'timestamp', 'identifier', 'rssi', 'distance', 'uid', 'data_type', 'occurrences'])

    # Preprocess data
    X = df[['timestamp', 'rssi', 'distance', 'occurrences']]  # Select relevant features
    y = df['data_type']  # Assuming 'data_type' is the target variable

    # Split data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Normalize data
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Train KMeans model
    kmeans = KMeans(n_clusters=3)  # Adjust the number of clusters as needed
    kmeans.fit(X_train)

    # Evaluate model
    y_pred = kmeans.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    logging.debug(f'Training accuracy: {accuracy}')

    # Save the trained model and scaler
    joblib.dump(scaler, 'models/scaler.pkl')
    joblib.dump(kmeans, 'models/kmeans_model.pkl')

    return jsonify({"message": "Model trained successfully!", "accuracy": accuracy})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

if __name__ == '__main__':
    logging.debug("Creating database tables if they don't exist...")
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracking_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                identifier TEXT,
                rssi INTEGER,
                distance REAL,
                uid TEXT,
                data_type TEXT,
                occurrences INTEGER,
                is_scanning BOOLEAN DEFAULT FALSE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        db.commit()
    logging.debug("Database tables created successfully.")
    logging.debug("Starting Flask app...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    logging.debug("Flask app started successfully.")
