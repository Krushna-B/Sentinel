from fastapi import FastAPI
from .database import Base, engine
from contextlib import asynccontextmanager
from .routers import state_vectors, orbits_vec
from .consumers.kafka_consumer import start_consumer

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_consumer()
    yield {}



app = FastAPI(lifespan=lifespan)
app.include_router(state_vectors.router)
app.include_router(orbits_vec.router)