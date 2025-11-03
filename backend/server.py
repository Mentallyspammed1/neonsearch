from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import httpx
import asyncio
from functools import lru_cache
import hashlib
from contextlib import asynccontextmanager
import random # Added for shuffling results

# Import video source drivers
from drivers import get_driver, get_all_drivers, DRIVER_REGISTRY


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging (ONLY ONCE)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# FastAPI lifespan manager (ONLY ONCE)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI app lifespan: startup") # Added log
    # Startup logic (if any)
    yield
    logger.info("FastAPI app lifespan: shutdown") # Added log
    client.close()

# Create the main app (ONLY ONCE)
app = FastAPI(lifespan=lifespan)

# CORS Middleware (apply to the ONE app instance)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ============================================
# Models
# ============================================

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class VideoSearchRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = ["all"]
    filters: Optional[Dict[str, Any]] = {}
    page: Optional[int] = 1
    limit: Optional[int] = 20

class Video(BaseModel):
    id: str
    title: str
    thumbnail: str
    url: str
    duration: Optional[str] = None
    views: Optional[str] = None
    rating: Optional[float] = None
    source: str
    upload_date: Optional[str] = None
    channel: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[Video]
    total: int
    page: int
    sources_searched: List[str]


# ============================================
# Cache and API Configuration
# ============================================

class SearchCache:
    """Simple in-memory LRU cache for search results"""
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def _make_key(self, query: str, sources: List[str], page: int) -> str:
        data = f"{query}:{','.join(sorted(sources))}:{page}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, query: str, sources: List[str], page: int) -> Optional[Dict]:
        key = self._make_key(query, sources, page)
        if key in self.cache:
            self.access_times[key] = datetime.now()
            logger.info(f"Cache hit for key: {key}") # Added log
            return self.cache[key]
        logger.info(f"Cache miss for key: {key}") # Added log
        return None
    
    def set(self, query: str, sources: List[str], page: int, data: Dict):
        key = self._make_key(query, sources, page)
        if len(self.cache) >= self.max_size:
            # Remove oldest accessed item
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        logger.info(f"Cache set for key: {key}")
        self.cache[key] = data
        self.access_times[key] = datetime.now()

search_cache = SearchCache()

# Initialize drivers dynamically
API_CONFIGS = {}
for name, driver_class in DRIVER_REGISTRY.items():
    driver = driver_class()
    API_CONFIGS[name] = {
        "enabled": True,
        "driver": driver,
        "base_url": getattr(driver, 'base_url', None) if hasattr(driver, 'base_url') else None
    }


# ============================================
# Video Search Logic
# ============================================

async def fetch_with_retry(url: str, params: dict, max_retries: int = 3) -> Optional[dict]:
    """Fetch data with exponential backoff retry"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries):
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch from {url} after {max_retries} attempts: {str(e)}", exc_info=True) # Added exc_info
                    return None
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed for {url}. Retrying in {2**attempt}s...") # Added log
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return None


async def search_source(source: str, query: str, page: int, limit: int) -> List[Video]:
    """Search a specific video source using its driver"""
    if source not in API_CONFIGS or not API_CONFIGS[source]["enabled"]:
        logger.debug(f"Source '{source}' is disabled or not found. Skipping.") # Added log
        return []
    
    config = API_CONFIGS[source]
    driver = config.get("driver")
    
    if not driver:
        logger.warning(f"No driver found for source: {source}")
        return []
    
    try:
        # Get the search URL from the driver
        search_url = driver.video_url(query, page)
        logger.info(f"Searching {source} at URL: {search_url}") # Added log
        
        # Fetch HTML content
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(search_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                html_content = response.text
                logger.debug(f"Successfully fetched HTML content from {source}.") # Added log
            except Exception as e:
                logger.error(f"Failed to fetch HTML from {source} at {search_url}: {str(e)}", exc_info=True) # Added exc_info
                return []
        
        # Parse results using driver's parser
        raw_results = driver.video_parser(html_content)
        logger.debug(f"Parsed {len(raw_results)} raw results from {source}.") # Added log
        
        # Convert to Video models
        videos = []
        for i, result in enumerate(raw_results[:limit]):
            try:
                video = Video(**result)
                videos.append(video)
            except Exception as e:
                logger.error(f"Error creating Video model for result #{i+1} from {source} (title: {result.get('title', 'N/A')}): {str(e)}", exc_info=True) # Added exc_info
                continue
        
        logger.info(f"Successfully processed {len(videos)} videos from {source}.") # Added log
        return videos
        
    except Exception as e:
        logger.error(f"An unexpected error occurred during search for {source}: {str(e)}", exc_info=True) # Added exc_info
        return []


# ============================================
# API Routes
# ============================================

@api_router.get("/")
async def root():
    logger.info("Root endpoint called.") # Added log
    return {"message": "Video Search API", "version": "1.0.0"}


@api_router.post("/search", response_model=SearchResponse)
async def search_videos(request: VideoSearchRequest):
    """
    Search videos across multiple sources
    
    - **query**: Search term (required)
    - **sources**: List of sources to search (default: all enabled)
    - **filters**: Additional filters (optional)
    - **page**: Page number for pagination
    - **limit**: Results per page
    """
    logger.info(f"Received search request: query='{request.query}', sources={request.sources}, page={request.page}, limit={request.limit}") # Added log
    try:
        sources_to_search = request.sources if request.sources and request.sources != ["all"] else list(API_CONFIGS.keys())
        
        # Check cache first
        cached_result = search_cache.get(request.query, sources_to_search, request.page)
        
        if cached_result:
            # Cache hit log is handled within search_cache.get
            return cached_result
        
        logger.info(f"Cache miss for query: {request.query}. Searching active sources: {sources_to_search}") # Added log
        
        # Filter enabled sources
        active_sources = [s for s in sources_to_search if s in API_CONFIGS and API_CONFIGS[s]["enabled"]]
        
        if not active_sources:
            logger.warning("No active video sources available for search.") # Added log
            raise HTTPException(status_code=400, detail="No active video sources available")
        
        # Search all sources concurrently
        logger.info(f"Initiating concurrent search for query '{request.query}' across sources: {active_sources}") # Added log
        search_tasks = [
            search_source(source, request.query, request.page, request.limit)
            for source in active_sources
        ]
        
        results = await asyncio.gather(*search_tasks)
        
        # Flatten and combine results
        all_videos = []
        for video_list in results:
            all_videos.extend(video_list)
        
        # Sort by relevance (you can implement custom scoring)
        # For now, just shuffle to mix sources
        random.shuffle(all_videos)
        
        # Apply pagination
        start_idx = (request.page - 1) * request.limit
        end_idx = start_idx + request.limit
        paginated_videos = all_videos[start_idx:end_idx]
        
        response = SearchResponse(
            results=paginated_videos,
            total=len(all_videos),
            page=request.page,
            sources_searched=active_sources
        )
        
        # Cache the result
        search_cache.set(request.query, sources_to_search, request.page, response.dict())
        
        logger.info(f"Search completed for query='{request.query}'. Found {len(paginated_videos)} results (total available: {len(all_videos)}).") # Modified log
        return response
        
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception during search for query='{request.query}': {http_exc.detail}", exc_info=True) # Added log
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred during search for query='{request.query}': {str(e)}", exc_info=True) # Added exc_info
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@api_router.get("/sources")
def get_sources_status(): # Changed from async def to def as it doesn't use await
    """Get available video sources and their status"""
    logger.info("Received request for available sources.") # Added log
    return {
        "sources": [
            {
                "name": name,
                "enabled": config["enabled"],
                "driver_name": config["driver"].name if config.get("driver") else name.title()
            }
            for name, config in API_CONFIGS.items()
        ]
    }


@api_router.post("/sources/{source_name}/toggle")
async def toggle_source(source_name: str):
    """Enable or disable a video source"""
    logger.info(f"Received request to toggle source: {source_name}") # Added log
    if source_name not in API_CONFIGS:
        logger.warning(f"Attempted to toggle unknown source: {source_name}") # Added log
        raise HTTPException(status_code=404, detail="Source not found")
    
    API_CONFIGS[source_name]["enabled"] = not API_CONFIGS[source_name]["enabled"]
    new_status = API_CONFIGS[source_name]["enabled"]
    logger.info(f"Toggled source '{source_name}'. New status: {'enabled' if new_status else 'disabled'}") # Added log
    return {
        "source": source_name,
        "enabled": new_status
    }


@api_router.get("/suggestions")
async def get_search_suggestions(q: str):
    """Get search suggestions based on query"""
    logger.info(f"Received request for search suggestions for query: '{q}'") # Added log
    # Mock suggestions - in production, use analytics or trending data
    suggestions = [
        f"{q} hd",
        f"{q} compilation",
        f"{q} amateur",
        f"{q} pov",
        f"best {q}"
    ]
    return {"suggestions": suggestions[:5]}


# Original routes
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    logger.info(f"Received request to create status check for client: {input.client_name}") # Added log
    status_obj = StatusCheck(**input.model_dump()) # Use model_dump directly for Pydantic v2
    
    doc = status_obj.model_dump()
    # Store timestamp as ISO string for easier MongoDB compatibility
    doc['timestamp'] = doc['timestamp'].isoformat() 
    
    try:
        await db.status_checks.insert_one(doc)
        logger.info(f"Successfully created status check with ID: {status_obj.id}") # Added log
    except Exception as e:
        logger.error(f"Failed to insert status check into MongoDB: {str(e)}", exc_info=True) # Added exc_info
        raise HTTPException(status_code=500, detail="Failed to save status check")
        
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    logger.info("Received request to retrieve status checks.") # Added log
    
    # Fetch from MongoDB
    try:
        status_checks_from_db = await db.status_checks.find().sort("timestamp", -1).limit(100).to_list(length=100)
        logger.info(f"Retrieved {len(status_checks_from_db)} status checks from MongoDB.") # Added log
    except Exception as e:
        logger.error(f"Failed to retrieve status checks from MongoDB: {str(e)}", exc_info=True) # Added exc_info
        raise HTTPException(status_code=500, detail="Failed to retrieve status checks")

    # Directly create StatusCheck objects, Pydantic will parse the timestamp string to datetime
    return [StatusCheck(**check) for check in status_checks_from_db]


# Include the router in the main app (apply to the ONE app instance)
app.include_router(api_router)