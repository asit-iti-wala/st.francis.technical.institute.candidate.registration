
from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone


# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main FastAPI app
app = FastAPI()

# Create a router with /api prefix
api_router = APIRouter(prefix="/api")


# ============================================
# PYDANTIC MODELS (Data Schemas)
# ============================================

class CandidateCreate(BaseModel):
    """Schema for creating a new candidate"""
    name: str
    surname: Optional[str] = ""
    trade: str
    year: int
    dob: str  # Date of birth as string (YYYY-MM-DD format)


class Candidate(BaseModel):
    """Schema for candidate with all fields"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    surname: Optional[str] = ""
    trade: str
    year: int
    dob: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================
# API ROUTES
# ============================================

@api_router.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "St. Francis Technical Institute API - Running"}


@api_router.post("/candidates", response_model=Candidate)
async def create_candidate(input: CandidateCreate):
    """
    Register a new candidate
    
    Request body example:
    {
        "name": "Rajesh Kumar",
        "surname": "Sharma",
        "trade": "Electrical",
        "year": 2024,
        "dob": "2005-05-15"
    }
    """
    try:
        # Create candidate object
        candidate_dict = input.model_dump()
        candidate_obj = Candidate(**candidate_dict)
        
        # Convert to dict and serialize datetime to ISO string for MongoDB
        doc = candidate_obj.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        
        # Insert into MongoDB
        await db.candidates.insert_one(doc)
        
        logging.info(f"New candidate registered: {candidate_obj.name}")
        return candidate_obj
        
    except Exception as e:
        logging.error(f"Error creating candidate: {e}")
        raise HTTPException(status_code=500, detail="Failed to register candidate")


@api_router.get("/candidates", response_model=List[Candidate])
async def get_candidates():
    """
    Get all registered candidates
    
    Returns: List of all candidates in the database
    """
    try:
        # Fetch all candidates from MongoDB (exclude MongoDB's _id field)
        candidates = await db.candidates.find({}, {"_id": 0}).to_list(1000)
        
        # Convert ISO string timestamps back to datetime objects
        for candidate in candidates:
            if isinstance(candidate.get('created_at'), str):
                candidate['created_at'] = datetime.fromisoformat(candidate['created_at'])
        
        logging.info(f"Retrieved {len(candidates)} candidates")
        return candidates
        
    except Exception as e:
        logging.error(f"Error fetching candidates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch candidates")


@api_router.delete("/candidates/{candidate_id}")
async def delete_candidate(candidate_id: str):
    """
    Delete a candidate by ID
    
    Parameters:
    - candidate_id: The unique ID of the candidate to delete
    """
    try:
        result = await db.candidates.delete_one({"id": candidate_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        logging.info(f"Candidate deleted: {candidate_id}")
        return {"message": "Candidate deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting candidate: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete candidate")


# ============================================
# APP CONFIGURATION
# ============================================

# Include the API router
app.include_router(api_router)

# Add CORS middleware (allows frontend to communicate with backend)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Shutdown event to close MongoDB connection
@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logging.info("MongoDB connection closed")


# ============================================
# RUN THE SERVER (for local development)
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)