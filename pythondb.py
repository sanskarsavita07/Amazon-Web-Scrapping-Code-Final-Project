# amazondb.py
import psycopg2
from psycopg2 import sql
from datetime import datetime

def create_db_connection(host, database, user, password):
    """
    Create and return a PostgreSQL database connection and cursor.
    """
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return None, None

def create_products_table(cursor, conn):
    """
    Create the 'products' table if it doesn't exist.
    Schema matches your Amazon Db.py so both scrapers use same table shape:
      id, product_name, product_price, page_number, scraped_at
    """
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                product_name TEXT,
                product_price TEXT,
                page_number INT,
                scraped_at TIMESTAMP,
                product_link TEXT,
                product_image TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Failed to create table: {e}")
        conn.rollback()

def clear_products_table(cursor, conn):
    """
    Remove all existing records from the products table.
    This ensures the table is empty before inserting new data.
    """
    try:
        cursor.execute("TRUNCATE TABLE products RESTART IDENTITY;")
        conn.commit()
        print("Cleared old product data before inserting new values.")
    except Exception as e:
        print(f"Failed to clear products table: {e}")
        conn.rollback()


def insert_products(cursor, conn, products_list):
    """
    Insert list of product dicts into the products table.
    Each product dict is expected to include:
      - product_name
      - product_price
      - page_number
      - timestamp 
      - product_link
      - product_image (will be stored in scraped_at)
    Extra keys in the dict (product_link/product_image) are ignored.
    """
    if not products_list:
        print("No products to insert.")
        return

    try:
        for product in products_list:
            cursor.execute("""
                INSERT INTO products (product_name, product_price, page_number, scraped_at, product_link, product_image)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                product.get('product_name'),
                product.get('product_price'),
                product.get('page_number'),
                product.get('timestamp'),
                product.get('product_link'),
                product.get('product_image')  # inserted into scraped_at
            ))
        conn.commit()
        print(f"{len(products_list)} products inserted successfully.")
    except Exception as e:
        print(f"Failed to insert bulk products: {e}")
        conn.rollback()
