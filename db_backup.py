import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime

def get_db_connection():
    """Return a connection to the PostgreSQL database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = psycopg2.connect(db_url)
    return conn

def get_backup_dir():
    """Create and return the backup directory path."""
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    return backup_dir

def create_backup():
    """Create a JSON backup of the database."""
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get all travelers
    cursor.execute('''
        SELECT id, first_name, last_name, telephone, email, house_number, registration_date, departure_date, is_active
        FROM traveler
    ''')
    travelers = [dict(row) for row in cursor.fetchall()]
    
    # Get booking sites for each traveler
    for traveler in travelers:
        cursor.execute('''
            SELECT bs.id, bs.name
            FROM booking_site bs
            JOIN traveler_booking_sites tbs ON bs.id = tbs.booking_site_id
            WHERE tbs.traveler_id = %s
        ''', (traveler['id'],))
        traveler['booking_sites'] = [dict(row) for row in cursor.fetchall()]
    
    # Get all booking sites
    cursor.execute('SELECT id, name FROM booking_site')
    booking_sites = [dict(row) for row in cursor.fetchall()]

    # Get all users (except passwords)
    cursor.execute('SELECT id, username, email FROM "user"')
    users = [dict(row) for row in cursor.fetchall()]
    
    # Create backup data
    backup_data = {
        'travelers': travelers,
        'booking_sites': booking_sites,
        'users': users,
        'backup_date': datetime.now().isoformat()
    }
    
    # Save to JSON file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = get_backup_dir()
    backup_file = os.path.join(backup_dir, f'travelers_backup_{timestamp}.json')
    
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=4, default=str)
    
    cursor.close()
    conn.close()
    return backup_file

def restore_from_backup(backup_file):
    """Restore database from a JSON backup file."""
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file {backup_file} not found")
    
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    
    # Create a connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Begin transaction
    conn.autocommit = False
    
    try:
        # Clear existing data
        cursor.execute('DELETE FROM traveler_booking_sites')
        cursor.execute('DELETE FROM traveler')
        
        # Don't delete booking sites or users, just make sure booking sites exist
        existing_sites = {}
        cursor.execute('SELECT id, name FROM booking_site')
        for row in cursor.fetchall():
            existing_sites[row[1]] = row[0]
        
        # Add booking sites that don't exist
        for site in backup_data['booking_sites']:
            if site['name'] not in existing_sites:
                cursor.execute('INSERT INTO booking_site (name) VALUES (%s) RETURNING id', (site['name'],))
                site_id = cursor.fetchone()[0]
                existing_sites[site['name']] = site_id
        
        # Restore travelers
        for traveler in backup_data['travelers']:
            # Convert registration_date to proper format if it's a string
            reg_date = traveler['registration_date']
            if isinstance(reg_date, str):
                # Try to parse the date format, it might be ISO format
                try:
                    dt = datetime.fromisoformat(reg_date)
                    reg_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    # If parsing fails, use current time
                    reg_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO traveler (id, first_name, last_name, telephone, email, house_number, 
                                     registration_date, departure_date, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                traveler['id'],
                traveler['first_name'],
                traveler['last_name'],
                traveler['telephone'],
                traveler['email'],
                traveler['house_number'],
                reg_date,
                traveler.get('departure_date'),  # Using get() to handle older backups without this field
                traveler.get('is_active', True)  # Default to True for older backups
            ))
            
            # Restore traveler's booking sites
            for site in traveler['booking_sites']:
                cursor.execute('''
                    INSERT INTO traveler_booking_sites (traveler_id, booking_site_id)
                    VALUES (%s, %s)
                ''', (traveler['id'], site['id']))
        
        # Reset sequence for traveler id
        cursor.execute('''
            SELECT setval('traveler_id_seq', (SELECT MAX(id) FROM traveler))
        ''')
        
        # Commit the transaction
        conn.commit()
        
    except Exception as e:
        # Roll back on error
        conn.rollback()
        cursor.close()
        conn.close()
        raise e
    
    cursor.close()
    conn.close()
    return True

def get_available_backups():
    """Return a list of available backup files."""
    backup_dir = get_backup_dir()
    backups = []
    
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.startswith('travelers_backup_') and file.endswith('.json'):
                backups.append(os.path.join(backup_dir, file))
    
    # Sort by modification time (newest first)
    backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return backups