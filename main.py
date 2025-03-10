import psycopg2
from psycopg2 import sql, connect

# Функция для удаления таблиц (если они существуют)
def drop_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS phones;
            DROP TABLE IF EXISTS clients;
        """)
        conn.commit()

def create_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clients(
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,

        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS phones(
        id SERIAL PRIMARY KEY,
        client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
        phone VARCHAR(20) UNIQUE NOT NULL
        );
        """)
        conn.commit()

def add_client(conn, first_name, last_name, email, phones=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO clients (first_name, last_name, email)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (first_name, last_name, email))
        client_id = cur.fetchone()[0]
        if phones:
            for phone in phones:
                cur.execute("""
                    INSERT INTO phones (client_id, phone)
                    VALUES (%s, %s);
                """, (client_id, phone))
        conn.commit()

def add_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO phones(client_id, phone)
        VALUES(%s, %s);
        """, (client_id, phone))
        conn.commit()

def change_client(conn, client_id, first_name=None, last_name=None, email=None, phones=None):
    with conn.cursor() as cur:
        update_fields = []
        if first_name:
            update_fields.append(('first_name', first_name))
        if last_name:
            update_fields.append(('last_name', last_name))
        if email:
            update_fields.append(('email', email))
        if update_fields:
            query = sql.SQL("UPDATE clients SET {} WHERE id = %s").format(
                sql.SQL(', ').join(
                    sql.SQL("{} = %s").format(sql.Identifier(field)) for field, value in update_fields
                )
            )
            cur.execute(query, [value for field, value in update_fields] + [client_id])
            conn.commit()

def delete_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute("""
        DELETE FROM phones
        WHERE client_id = %s AND phone = %s;
        """, (client_id, phone))
        conn.commit()
def delete_client(conn, client_id):
    with conn.cursor() as cur:
        cur.execute("""
        DELETE FROM clients
        WHERE id = %s;
        """, (client_id,))
        conn.commit()

def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    with conn.cursor() as cur:
        conditions = []
        if first_name:
            conditions.append(('first_name', first_name))
        if last_name:
            conditions.append(('last_name', last_name))
        if email:
            conditions.append(('email', email))
        if phone:
            conditions.append(('phone', phone))
        if conditions:
            query = sql.SQL(
                "SELECT c.id, c.first_name, c.last_name, c.email, p.phone FROM clients c LEFT JOIN phones p ON c.id = p.client_id WHERE {}").format(
                sql.SQL(' OR ').join(
                    sql.SQL("{} = %s").format(sql.Identifier(field)) for field, value in conditions
                )
            )
            cur.execute(query, [value for field, value in conditions])
            return cur.fetchall()
        return []


with psycopg2.connect(database="clients", user="postgres", password="password") as conn:
    # Удаляем таблицы (если они существуют)
    drop_tables(conn)
    print("Таблицы удалены")
    create_db(conn)
    add_client(conn, "Дмитрий", "Сарделькин", "sardelya@example.com", ["1234567890", "0987654321"])
    add_phone(conn, 1, "5555555555")
    change_client(conn, 1, first_name="Иван")
    delete_phone(conn, 1, "0987654321")
    print(find_client(conn, first_name="Иван"))
    delete_client(conn, 1)

conn.close()