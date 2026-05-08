from dotenv import load_dotenv
from pathlib import Path
import os, psycopg2

load_dotenv(Path(__file__).parent / ".env")

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST','localhost'),
        port=os.getenv('DB_PORT','5432'),
        dbname=os.getenv('DB_NAME','webgis'),
        user=os.getenv('DB_USER','postgres'),
        password=os.getenv('DB_PASS','postgres'),
        connect_timeout=5
    )
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM poi')
    print('poi:', cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM roads')
    print('roads:', cur.fetchone()[0])
    conn.close()
    print('DB OK')
except Exception as e:
    print('ERROR:', e)