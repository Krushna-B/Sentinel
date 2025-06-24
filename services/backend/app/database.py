from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base



DATABASE_URL = "postgresql://orbit:orbit@postgres:5432/orbit"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, autocommit = False, autoflush = False)    #Creates class with pre-configuration for database 
Base = declarative_base() # Creates superclass for ORM to map variables to table columns 

'''Creats Database session and waits for response to close (yield)'''
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


 

