# backend/app/routers/zeek.py (MODIFIED)

from fastapi import APIRouter
from typing import List
from app.services import ids_query_service
from app import schemas

# --- START OF CACHING FIX ---
from fastapi_cache.decorator import cache
# --- END OF CACHING FIX ---


router = APIRouter()


@router.get("/connections", response_model=List[schemas.ZeekConnectionSchema], tags=["Zeek"])
async def get_zeek_connections():
    """
    Returns the most recent connection logs captured by Zeek from Elasticsearch.
    """
    # Increased limit to provide a better dataset for the frontend chart.
    connections = ids_query_service.get_latest_zeek_connections(limit=1000)
    return connections


# ### --- START OF CACHING FIX --- ###
# This endpoint is now cached for 60 seconds. The slow query will only run
# once per minute, making the UI feel instantly responsive on reloads.
@router.get("/protocol-distribution", response_model=List[schemas.ProtocolDistribution], tags=["Zeek"])
@cache(expire=60) # Cache the result of this function for 60 seconds
async def get_zeek_protocol_distribution():
    """
    Returns the top 10 most used protocols by traffic volume from Zeek data in Elasticsearch.
    """
    protocol_distribution = ids_query_service.get_zeek_protocol_distribution(limit=5)
    return protocol_distribution
# ### --- END OF CACHING FIX --- ###
