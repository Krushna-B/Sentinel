from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base



DATABASE_URL = "postgresql://user:password@localhost:5432/telemetry"

engine = create_engine(DATABASE_URL, echo=True)
session = sessionmaker(engine, autocommit = False, autoflush = False)    #Creates class with pre-configuration for database 
Base = declarative_base() # Creates superclass for ORM to map variables to table columns 

'''Creats Database session and waits for response to close (yield)'''
def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


 

