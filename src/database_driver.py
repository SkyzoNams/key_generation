from psycopg2.pool import SimpleConnectionPool
import sys

""""
This class is used to connect to a PostgreSQL database.

The class can be initialized with the following parameters:
    user: str = None,
    password: str = None,
    host: str = None,
    port: str = None,
    database: str = None

If any of the parameters are not provided, the class will attempt to import the Config class from the Config.py file.
If the Config class is not found, the class will return an error.

The Config class must return the following values:
    database_user: str
    database_password: str
    database_host: str
    database_port: str
    database_database: str

The class has the following methods:
    execute(execution_string: str, commit: bool, fetch_one: bool = None, fetch_all: bool = None)

The execute method takes the following parameters:
    execution_string: str
    commit: bool
    fetch_one: bool = None
    fetch_all: bool = None

The execution_string parameter is the SQL query that will be executed.
The commit parameter is a boolean that determines whether or not the query will be committed.
The fetch_one parameter is a boolean that determines whether or not the query will return one row.
The fetch_all parameter is a boolean that determines whether or not the query will return all rows.

The execute method returns the following values:
    "executed command"
    fetch
    e

If the commit parameter is True, the method will return "executed command".
If the fetch_one parameter is True, the method will return the first row of the query.
If the fetch_all parameter is True, the method will return all rows of the query.
If an error occurs, the method will return the error.

-------------------------------------------get_insert_string------------------------------------------------------------

This function is used to create an insert string for a given table.
    The insert string is used to insert data into a table.
    The function takes a table name as an argument and returns an insert string.
    The insert string is created by selecting the column names from the table.
    The column names are then used to create the insert string.
    The insert string is then returned.
    
-------------------------------------------check_for_existence----------------------------------------------------------

Checks for the existence of a row in the database.
    :param where_var: The column to check for existence.
    :param from_var: The lower bound of the range to check for existence.
    :param to_var: The upper bound of the range to check for existence.
    :param conditional_var: The value to check for existence.
    :return: True if the row exists, False otherwise.
"""


class DatabaseDriver(object):
    def __init__(
            self,
            user: str = None,
            password: str = None,
            host: str = None,
            port: str = None,
            database: str = None):
        if None in [user, password, host, port, database]:
            self.import_config()
        else:
            self.user = user
            self.password = password
            self.host = host
            self.port = port
            self.database = database
            self.maxcon = 10
            self.mincon = 0
        
    def import_config(self):
        try:
            from key_generation.src.Config import Config
        except Exception as e:
            try:
                from src.Config import Config
            except Exception as e:
                raise e

        if "key_generation.src.Config" in sys.modules.keys() or "src.Config" in sys.modules.keys():
            self.user = Config().return_config_database(database_user=True)
            self.password = Config().return_config_database(database_password=True)
            self.host = Config().return_config_database(database_host=True)
            self.port = Config().return_config_database(database_port=True)
            self.database = Config().return_config_database(database_database=True)
            self.maxcon = Config().return_config_database(database_max_connection=True)
            self.mincon = Config().return_config_database(database_min_connection=True)
        else:
            print("keys not found")

    def execute(
            self,
            execution_string: str,
            item_tuple: tuple = None,
            commit: bool = None,
            fetch_one: bool = None,
            fetch_all: bool = None):
        if None in [fetch_one, fetch_all]:
            if len(execution_string.strip(" ")) != 0:
                try:
                    self.connect()
                    if item_tuple is not None:
                        self.cursor.execute(execution_string, item_tuple)
                    else:
                        self.cursor.execute(execution_string)
                    if commit:
                        self.connection.commit()
                        self.disconnect()
                        return "executed command"
                    if fetch_one:
                        fetch = self.cursor.fetchone()
                        self.disconnect()
                        return fetch
                    if fetch_all:
                        fetch = self.cursor.fetchall()
                        self.disconnect()
                        return fetch
                except Exception as e:
                    raise e
            else:
                return "Cannot execute an empty query"
        else:
            return "Cannot fetch one and both at the same time"

    def connect(self):
        try:
            self.pgpool = SimpleConnectionPool(minconn=self.mincon, maxconn=self.maxcon, host=self.host,
                                               database=self.database,
                                               user=self.user,
                                               password=self.password, port=self.port, connect_timeout=30)
            self.connection = self.pgpool.getconn()
            self.cursor = self.connection.cursor()
        except Exception as e:
            raise e

    def disconnect(self):
        self.pgpool.closeall()


if __name__ == '__main__':
    print("On Main")
