import os
import psycopg
from psycopg.rows import dict_row
from faker import Faker
import random
import uuid
from dotenv import load_dotenv

load_dotenv('.env', override=True)

# Database connection parameters
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DB = os.getenv('POSTGRES_DB')

# Number of records
NUM_CUSTOMERS = 100
NUM_PURCHASES = 1000
PRODUCTS = [
    "Laptop", "Smartphone", "Headphones", 
    "Monitor", "Keyboard", "Mouse", "Tablet", 
    "Camera", "Smartwatch", "Printer"
]

fake = Faker()

def create_database_if_not_exists():
    """
    Checks if the target PostgreSQL database exists; creates it if not.

    Connects to the default 'postgres' database with autocommit enabled.
    Executes a query to verify the existence of the database specified by
    'POSTGRES_DB'. If it does not exist, creates the database.

    Uses psycopg for database connection and executes SQL commands.
    """
    with psycopg.connect(
        dbname="postgres",
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        autocommit=True
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (POSTGRES_DB,))
            if not cur.fetchone():
                cur.execute(f"CREATE DATABASE {POSTGRES_DB}")
                print(f"Database '{POSTGRES_DB}' created.")
            else:
                print(f"Database '{POSTGRES_DB}' already exists.")

def create_tables():
    """
    Creates the 'customer' and 'purchase' tables in the database if they do not already exist.

    Uses SQL CREATE TABLE IF NOT EXISTS statements to define the schema for each table.
    Establishes a database connection and executes the creation commands within a transaction context.
    """
    create_customer_table = """
    CREATE TABLE IF NOT EXISTS customer (
        customer_id VARCHAR(100) PRIMARY KEY,
        customer_name VARCHAR(100),
        email_address VARCHAR(100) UNIQUE,
        contact_number VARCHAR(50),
        date_of_birth DATE,
        address TEXT
    );
    """
    create_purchase_table = """
    CREATE TABLE IF NOT EXISTS purchase (
        purchase_id VARCHAR(100) PRIMARY KEY,
        customer_id VARCHAR(100) REFERENCES customer(customer_id),
        product_name VARCHAR(100),
        price NUMERIC(10, 2),
        quantity_purchased INTEGER,
        purchase_date TIMESTAMP
    );
    """
    with psycopg.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(create_customer_table)
            cur.execute(create_purchase_table)
            conn.commit()
        print("Tables created (if not existing).")

def generate_customers(n):
    customers = []
    for _ in range(n):
        bday = fake.date_of_birth(minimum_age=18, maximum_age=100)
        bday = bday.strftime("%Y-%m-%d")

        customers.append({
            "customer_id": str(uuid.uuid4()),
            "customer_name": fake.name(),
            "email_address": fake.unique.email(),
            "contact_number": fake.phone_number(),
            "date_of_birth": bday,
            "address": fake.address().replace("\n", ", ")
        })
    return customers

def insert_customers(customers):
    ids = []
    with psycopg.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
    ) as conn:
        with conn.cursor() as cur:
            for c in customers:
                cur.execute(
                    """
                    INSERT INTO customer (
                        customer_id, customer_name, email_address, 
                        contact_number, date_of_birth, address
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING customer_id
                    """,
                    (c["customer_id"], c["customer_name"], c["email_address"], 
                     c["contact_number"], c["date_of_birth"], c["address"])
                )
                ids.append(cur.fetchone()[0])
            conn.commit()
    return ids

def generate_purchases(customer_ids, n):
    """
    Generate a list of purchase records for synthetic data population.

    Parameters
    ----------
    customer_ids : list of str
        List of customer IDs to associate each purchase with a customer.
    n : int
        Number of purchase records to generate.

    Returns
    -------
    list of dict
        A list containing dictionaries, each representing a purchase record
    """
    purchases = []
    for _ in range(n):
        customer_id = random.choice(customer_ids)
        product = random.choice(PRODUCTS)
        price = round(random.uniform(10, 2000), 2)
        quantity = random.randint(1, 5)
        purchase_date = fake.date_time_between(start_date='-2y', end_date='now')
        purchase_date = purchase_date.strftime("%Y-%m-%d %H:%M:%S")
        
        purchases.append({
            "purchase_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "product_name": product,
            "price": price,
            "quantity_purchased": quantity,
            "purchase_date": purchase_date
        })
    return purchases

def insert_purchases(purchases):
    """
    Insert purchase records into the 'purchase' table.

    Parameters
    ----------
    purchases : list of dict
        A list of dictionaries, each representing a purchase record

    Returns
    -------
    None
    """
    with psycopg.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
    ) as conn:
        with conn.cursor() as cur:
            for p in purchases:
                cur.execute(
                    """
                    INSERT INTO purchase (
                        purchase_id, customer_id, product_name, 
                        price, quantity_purchased, purchase_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (p["purchase_id"], p["customer_id"], p["product_name"], 
                     p["price"], p["quantity_purchased"], p["purchase_date"])
                )
            conn.commit()

if __name__ == "__main__":
    create_database_if_not_exists()
    create_tables()
    customers = generate_customers(NUM_CUSTOMERS)
    customer_ids = insert_customers(customers)
    purchases = generate_purchases(customer_ids, NUM_PURCHASES)
    insert_purchases(purchases)
    print(f"Inserted {len(customers)} customers and {len(purchases)} purchases into '{POSTGRES_DB}'.")
