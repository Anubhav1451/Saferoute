from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router

app = FastAPI(
    title="SafeRoute AI API",
    description="Smart navigation API with safety scores, crime data, and environmental factors",
    version="0.1.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "healthy", "service": "saferoute-ai-api"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SafeRoute AI API",
        "version": "0.1.0",
        "docs": "/docs"
    }
