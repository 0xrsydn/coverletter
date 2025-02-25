from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

# Internal imports
from config import load_config
from api.routes import document_routes, job_routes, company_routes 

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Create FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI"}

# Include routers with their original paths
# No prefix is used since we've updated the route paths to match original endpoints
app.include_router(document_routes.router, tags=["Document Processing"])
app.include_router(job_routes.router, tags=["Job Analysis"])
app.include_router(company_routes.router, tags=["Company Analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
