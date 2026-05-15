from sqlmodel import create_engine, Session, SQLModel
from .config import settings


engine = create_engine(
    settings.DATABASE_URL,
    echo= settings.DEBUG,
    pool_pre_ping= True,
    )

"""
dependencia para generar la sesion de db
"""

def get_db():
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


"""
dependencia para DatabaseScheduler
def dbs_session():
    return Session(engine)

"""