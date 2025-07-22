from fastapi import FastAPI
from .database import Base, engine
from contextlib import asynccontextmanager
from .routes import state_vectors
from .consumers.kafka_consumer import start_consumer

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_consumer()
    yield {}



app = FastAPI(lifespan=lifespan)
app.include_router(state_vectors.router)