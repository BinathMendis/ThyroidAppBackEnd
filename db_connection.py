import pyodbc

def get_db_connection():
    conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=BINATH\SQLEXPRESS;"  # Replace with your server name (e.g., 'localhost' or 'SQLSERVER')
        "DATABASE=Research_Thyroid;"      # Replace with your database name
        "Trusted_Connection=yes;"    # Use Windows Authentication (no username/password)
    )
    return conn
