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

# Import video source drivers
from drivers import get_driver, get_all_drivers, DRIVER_REGISTRY


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

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

class APIConfig(BaseModel):
    name: str
    enabled: bool
    base_url: Optional[str] = None
    api_key: Optional[str] = None


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
            return self.cache[key]
        return None
    
    def set(self, query: str, sources: List[str], page: int, data: Dict):
        key = self._make_key(query, sources, page)
        if len(self.cache) >= self.max_size:
            # Remove oldest accessed item
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
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
                    logger.error(f"Failed to fetch from {url} after {max_retries} attempts: {str(e)}")
                    return None
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return None


def create_mock_videos(query: str, source: str, count: int = 10) -> List[Video]:
    """Generate mock video data for demonstration"""
    videos = []
    for i in range(count):
        video = Video(
            id=f"{source}_{query}_{i}_{uuid.uuid4().hex[:8]}",
            title=f"{query.title()} - Video {i+1} from {source.title()}",
            thumbnail=f"https://picsum.photos/seed/{source}{i}/320/180",
            url=f"https://{source}.com/view/{uuid.uuid4().hex}",
            duration=f"{5 + (i % 30)}:{10 + (i % 50):02d}",
            views=f"{(i+1) * 1000 + (i % 999):,}",
            rating=round(3.5 + (i % 3) * 0.5, 1),
            source=source,
            upload_date="2 days ago" if i % 3 == 0 else "1 week ago",
            channel=f"{source.title()} Channel {i % 5 + 1}"
        )
        videos.append(video)
    return videos


async def search_source(source: str, query: str, page: int, limit: int) -> List[Video]:
    """Search a specific video source using its driver"""
    if source not in API_CONFIGS or not API_CONFIGS[source]["enabled"]:
        return []
    
    config = API_CONFIGS[source]
    driver = config.get("driver")
    
    if not driver:
        logger.warning(f"No driver found for source: {source}")
        return []
    
    try:
        # Get the search URL from the driver
        search_url = driver.video_url(query, page)
        
        # Fetch HTML content
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(search_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                html_content = response.text
            except Exception as e:
                logger.error(f"Failed to fetch from {source}: {str(e)}")
                return []
        
        # Parse results using driver's parser
        raw_results = driver.video_parser(html_content)
        
        # Convert to Video models
        videos = []
        for result in raw_results[:limit]:
            try:
                video = Video(**result)
                videos.append(video)
            except Exception as e:
                logger.error(f"Error creating Video model: {str(e)}")
                continue
        
        return videos
        
    except Exception as e:
        logger.error(f"Error searching {source}: {str(e)}")
        return []


# ============================================
# API Routes
# ============================================

@api_router.get("/")
async def root():
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
    try:
        # Check cache first
        sources_to_search = request.sources if request.sources and request.sources != ["all"] else list(API_CONFIGS.keys())
        cached_result = search_cache.get(request.query, sources_to_search, request.page)
        
        if cached_result:
            logger.info(f"Cache hit for query: {request.query}")
            return cached_result
        
        # Filter enabled sources
        active_sources = [s for s in sources_to_search if s in API_CONFIGS and API_CONFIGS[s]["enabled"]]
        
        if not active_sources:
            raise HTTPException(status_code=400, detail="No active video sources available")
        
        # Search all sources concurrently
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
        import random
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
        
        logger.info(f"Search completed: query='{request.query}', results={len(paginated_videos)}")
        return response
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@api_router.get("/sources")
async def get_sources():
    """Get available video sources and their status"""
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
    if source_name not in API_CONFIGS:
        raise HTTPException(status_code=404, detail="Source not found")
    
    API_CONFIGS[source_name]["enabled"] = not API_CONFIGS[source_name]["enabled"]
    return {
        "source": source_name,
        "enabled": API_CONFIGS[source_name]["enabled"]
    }


@api_router.get("/suggestions")
async def get_search_suggestions(q: str):
    """Get search suggestions based on query"""
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
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks


# Include the router in the main app
app.include_router(api_router)

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
