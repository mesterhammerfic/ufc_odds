import psycopg2

PORT = local.port
USER = local.user
HOST = local.host
PASSWORD = local.password



conn = psycopg2.connect(dbname=DBNAME, port=PORT, user=USER, host=HOST, password=PASSWORD)