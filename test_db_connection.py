import psycopg2
import os

# Database credentials
db_params = {
    'dbname': os.getenv('DATABASE_NAME'),
    'user': os.getenv('DATABASE_USER'),
    'password': os.getenv('AIVEN_SERVICE_PASSWORD'),
    'host': os.getenv('DATABASE_HOST'),
    'port': os.getenv('DATABASE_PORT')
}

print("Attempting to connect to the database...")

try:
    # Try to establish a connection
    conn = psycopg2.connect(**db_params)
    
    # Create a cursor
    cursor = conn.cursor()
    
    # Execute a simple query
    cursor.execute("SELECT version();")
    
    # Fetch the result
    version = cursor.fetchone()
    print(f"Connection successful! PostgreSQL version: {version[0]}")
    
    # Close the cursor and connection
    cursor.close()
    conn.close()
    print("Connection closed.")
    
except Exception as e:
    print(f"Error connecting to the database: {e}")
