from sqlalchemy import create_engine, MetaData, Table, Column, Boolean

# Create the database engine
engine = create_engine('sqlite:///tracking_data.db')

# Create the metadata object
metadata = MetaData()

# Reflect the existing table
metadata.reflect(bind=engine)
tracking_data = Table('tracking_data', metadata, autoload_with=engine)

# Check if 'is_scanning' column already exists
if 'is_scanning' not in tracking_data.columns:
    with engine.connect() as conn:
        conn.execute('ALTER TABLE tracking_data ADD COLUMN is_scanning BOOLEAN DEFAULT FALSE')

print("Schema updated successfully!")
