from src.db_client.db_client import DBClient, DBClientModel


def cli() -> None:
    db = DBClient().prepare_database()
