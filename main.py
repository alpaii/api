from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import composers
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Classical Album Management API",
    description="API for managing classical music composers and albums",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(composers.router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "Classical Album Management API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
