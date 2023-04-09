import psycopg2
from pydantic import BaseModel
from typing import List

from src.db_client.models.aois import AOI
from src.db_client.models.files import File

from settings import DATABASE, USER, PASSWORD, HOST, PORT
from .prepare_database_commands import create_table_commands, add_test_data
from .models.users import User


class DBClientModel(BaseModel):
    database: str = DATABASE
    user: str = USER
    password: str = PASSWORD
    host: str = HOST
    port: str = PORT


class DBClient:
    database = DATABASE
    user = USER
    password = PASSWORD
    host = HOST
    port = PORT

    def _connect(self):
        """
        Connect to the main database.

        Returns
        -------
        psycopg2.connect
        """
        conn = psycopg2.connect(
            database=self.database,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )
        conn.autocommit = True

        return conn

    def _execute_for_prepare_database(self, curr, command):
        try:
            curr.execute(command)
        except psycopg2.errors.DuplicateDatabase:
            print("Database waterpix already created")
        except psycopg2.errors.DuplicateSchema:
            print("Schema drought already created")
        except psycopg2.errors.DuplicateTable:
            print("Table already created")
        except psycopg2.errors.DuplicateObject:
            print("PostGIS extension already added")
        except Exception as e:
            raise e

    def _execute_get(self, command):
        try:
            db = self._connect()
            curr = db.cursor()
            curr.execute(command)
            return curr.fetchall()
        except Exception as e:
            raise e
        finally:
            curr.close()
            db.close()

    def _execute_insert(self, command, values):
        try:
            db = self._connect()
            curr = db.cursor()
            curr.execute(command, values)
            db.commit()
        except Exception as e:
            raise e
        finally:
            curr.close()
            db.close()

    def prepare_database(self) -> None:
        """
        Creates the database for our project.
        In future, it will be used to create tables and other stuff.
        """
        # there is no our database, so we need to connect to postgres DB first
        self.database = "postgres"
        db = self._connect()
        curr = db.cursor()
        self._execute_for_prepare_database(curr, """CREATE database drought;""")
        curr.close()
        db.close()

        self.database = DATABASE
        db = self._connect()
        curr = db.cursor()

        self._execute_for_prepare_database(curr, """CREATE SCHEMA drought;""")
        self._execute_for_prepare_database(curr, """CREATE EXTENSION postgis;""")

        for command in create_table_commands:
            self._execute_for_prepare_database(curr, command)

        for command in add_test_data:
            self._execute_for_prepare_database(curr, command)

        curr.close()
        db.close()

    def get_all_aois(self) -> List[AOI]:
        command = """
        SELECT geom_id, order_id, ST_AsText(geom), ST_SRID(geom) FROM drought.aois
        """
        result = self._execute_get(command)

        return [
            AOI(geom_id=aoi[0], order_id=aoi[1], geometry=aoi[2], epsg=aoi[3])
            for aoi in result
        ]

    def get_all_aois_for_user(self, user_id: int) -> List[AOI]:
        command = f"""
        SELECT aois.geom_id, aois.order_id, ST_AsText(aois.geom), ST_SRID(aois.geom)
        FROM drought.aois
        LEFT JOIN drought.orders ON aois.order_id = orders.order_id
        WHERE orders.user_id = {user_id}
        """
        result = self._execute_get(command)

        return [
            AOI(geom_id=aoi[0], order_id=aoi[1], geometry=aoi[2], epsg=aoi[3])
            for aoi in result
        ]

    def insert_file(self, file: File) -> None:
        # make path relative to waterpix-backend
        file.make_path_relative()

        command = """INSERT INTO drought.files (order_id, geom_id, path, wq_index, file_extension, date)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        values = (
            file.order_id,
            file.geom_id,
            str(file.path),
            file.wq_index,
            file.file_extension,
            file.date.strftime("%Y-%m-%d 00:00:00"),
        )

        self._execute_insert(command, values)
        print(
            f"    Inserted produced TIF for {file.wq_index} AOI {file.order_id} to DB"
        )

    def get_user(self, username: str) -> User:
        command = f"SELECT * FROM drought.users WHERE username='{username}'"
        result = self._execute_get(command)

        users = [
            User(
                user_id=user[0],
                username=user[1],
                password=user[2],
                email=user[3],
                phone=user[4],
                disabled=user[5],
            )
            for user in result
        ]
        if len(users) > 1:
            raise ValueError("Returned more than 1 user from DB")

        return users[0]
