from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_database, close_database
from app.routers import health, recommendations, tenants

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB connection
    get_database()
    yield
    # Shutdown: Close MongoDB connection
    await close_database()

app = FastAPI(
    title="Entry Recommendation Service",
    description="Multi-Tenant Behavioral Recommendations & Smart Retrieval for Events",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(recommendations.router)
app.include_router(tenants.router)
