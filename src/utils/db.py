import psycopg2

def init_db(database, user, password, host, port, max_obs_size):
    print("Setting up the database...")
    print(f"Connecting to database {database} on {host} as user {user}")
    print(f"Password: {password}")
    
    # connect to the database
    conn = psycopg2.connect(
        dbname=database,
        user=user,
        password=password,
        host=host,
        port=port
    )

    cursor = conn.cursor()

    # delete table if it exists (number of columns may have changed)
    cursor.execute("DROP TABLE IF EXISTS microgrid_data;")

    # create table if it doesn't exist
    table_def = "CREATE TABLE IF NOT EXISTS microgrid_data ("
    table_def += "timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, "
    table_def += "tenant_id VARCHAR NOT NULL, "

    for i in range(max_obs_size):
        table_def += f"obs_{i} DOUBLE PRECISION, "

    table_def += "PRIMARY KEY (timestamp)"
    table_def += ");"

    cursor.execute(table_def)

    # create index
    cursor.execute("CREATE INDEX ON microgrid_data (tenant_id);")

    # check if it's a hypertable
    cursor.execute('''
        SELECT EXISTS (
            SELECT 1
            FROM   pg_catalog.pg_class c
            JOIN   pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE  n.nspname = 'public'
            AND    c.relname = 'microgrid_data'
            AND    c.relkind = 'r'
        );
    ''')
    
    is_hypertable = cursor.fetchone()[0]
    
    if not is_hypertable:
        print("Creating hypertable...")
        cursor.execute("SELECT create_hypertable('microgrid_data', 'timestamp');")

    # commit changes and close the connection
    conn.commit()
    return conn, cursor


def get_db_conn(database, user, password, host, port, max_obs_size):
    print(f"Connecting to database {database} on {host} as user {user}")
    print(f"Password: {password}")

    conn = psycopg2.connect(
        dbname=database,
        user=user,
        password=password,
        host=host,
        port=port
    )

    return conn, conn.cursor()
