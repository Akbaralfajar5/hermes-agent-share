# PostgreSQL Management (from postgres-management skill)

## Installation
```bash
sudo apt update && sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql && sudo systemctl enable postgresql
```

## Basic Operations
```bash
sudo -u postgres psql
CREATE DATABASE mydb;
CREATE USER myuser WITH PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
\l  -- list databases
\dt -- list tables
\q  -- quit
```

## Connection String
```
postgresql://username:password@localhost:5432/database_name
```

## Common SQL
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CRUD
INSERT INTO users (email, name) VALUES ('user@example.com', 'John');
SELECT * FROM users WHERE email = 'user@example.com';
UPDATE users SET name = 'Jane' WHERE id = 1;
DELETE FROM users WHERE id = 1;

-- Index
CREATE INDEX idx_users_email ON users(email);
```

## Backup & Restore
```bash
pg_dump -U myuser -d mydb > backup.sql
pg_dump -U myuser -d mydb | gzip > backup.sql.gz
psql -U myuser -d mydb < backup.sql
pg_dump -U myuser -Fc mydb > backup.dump
pg_restore -U myuser -d mydb backup.dump
```

## Remote Access
```bash
# /etc/postgresql/15/main/postgresql.conf
listen_addresses = '*'

# /etc/postgresql/15/main/pg_hba.conf
host all all 0.0.0.0/0 md5

sudo systemctl restart postgresql
```

## Performance
```sql
-- Slow queries
SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;

-- Kill query
SELECT pg_terminate_backend(pid);

-- Maintenance
VACUUM ANALYZE users;

-- Sizes
SELECT pg_size_pretty(pg_total_relation_size('users'));
SELECT pg_size_pretty(pg_database_size('mydb'));
```

## Python Integration
```python
import psycopg2
conn = psycopg2.connect(host="localhost", database="mydb", user="myuser", password="mypassword")
cur = conn.cursor()
cur.execute("SELECT * FROM users")
rows = cur.fetchall()
conn.close()
```

## Docker Setup
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
```

## Troubleshooting
```bash
sudo tail -f /var/log/postgresql/postgresql-15-main.log
SELECT * FROM pg_stat_activity;  -- connections
SELECT * FROM pg_locks;          -- locks
ALTER USER myuser WITH PASSWORD 'newpassword';  -- reset password
```
