import mysql.connector
from config import Config

def update_ingredients(cursor):
    # Select rows where 'item' starts with '- '
    select_query = "SELECT id, item FROM ingredients WHERE item LIKE '- %'"
    cursor.execute(select_query)
    rows = cursor.fetchall()

    # Update each row
    for row in rows:
        id, item = row
        new_item = item[2:]  # Remove the '- ' prefix
        update_query = "UPDATE ingredients SET item = %s WHERE id = %s"
        cursor.execute(update_query, (new_item, id))
    print(f"Updated {len(rows)} rows.")

def main():
    db_config = {
        'host': Config.DB_HOST,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME
    }

    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        update_ingredients(cursor)  # Call the update function
        
        connection.commit()  # Commit the changes
        print("Ingredient items updated successfully.")
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()
