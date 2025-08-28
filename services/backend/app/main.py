from fastapi import FastAPI
from .database import Base, engine
from contextlib import asynccontextmanager
from .routers import health, routes
from fastapi.middleware.cors import CORSMiddleware

DEV_ORIGINS = [
    "http://localhost:3000/globe",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
PROD_ORIGINS = [
    "https://sentinel-v0.vercel.app"
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield {}


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,          
    allow_methods=["GET","POST" "OPTIONS"],   
    allow_headers=["authorization", "content-type"],
    allow_credentials=False,            # True only if you use cookies
)

app.include_router(health.router)
app.include_router(routes.router)