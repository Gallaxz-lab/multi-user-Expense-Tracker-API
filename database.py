import psycopg

def get_db_connection():
    return psycopg.connect(
        host="127.0.0.1",
        port="5432",
        dbname="expense_tracker",
        user="postgres",
        password="@Won083104"
        )
