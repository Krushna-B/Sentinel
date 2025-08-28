from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")



if (DATABASE_URL is None):
    pass
else:
    engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(engine, autocommit = False, autoflush = False)    #Creates class with pre-configuration for database 
Base = declarative_base() 

'''Creats Database session and waits for response to close (yield)'''
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


 


