from fastapi import FastAPI
from .database import Base, engine
from contextlib import asynccontextmanager
from .routers import routes, state_vectors
from .consumers.kafka_consumer import start_consumer
from fastapi.middleware.cors import CORSMiddleware

DEV_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_consumer()
    yield {}


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,          # be explicit; don't use "*" in prod
    allow_methods=["GET", "OPTIONS"],   # add POST/PUT/DELETE if you use them
    allow_headers=["authorization", "content-type"],
    allow_credentials=False,            # True only if you use cookies
)



app.include_router(state_vectors.router)
app.include_router(routes.router)