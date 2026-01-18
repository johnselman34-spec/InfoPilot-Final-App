"""
InfoPilot Explorer - Elasticsearch Integration
Semantic search and document indexing with Elasticsearch
"""
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
import hashlib

logger = logging.getLogger(__name__)

# Elasticsearch configuration
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "https://my-elasticsearch-project-bddd81.es.us-central1.gcp.elastic-cloud.com")
ELASTICSEARCH_API_KEY = os.environ.get("ELASTICSEARCH_API_KEY", "")

# Index names
SEARCH_RESULTS_INDEX = "infopilot-search-results"
PROTOCOLS_INDEX = "infopilot-protocols"

# Elasticsearch client (lazy initialization)
_es_client = None


def get_elasticsearch_client():
    """Get or create Elasticsearch client."""
    global _es_client
    
    if _es_client is not None:
        return _es_client
    
    if not ELASTICSEARCH_API_KEY:
        logger.warning("Elasticsearch API key not configured")
        return None
    
    try:
        from elasticsearch import Elasticsearch
        
        _es_client = Elasticsearch(
            ELASTICSEARCH_URL,
            api_key=ELASTICSEARCH_API_KEY,
            request_timeout=30,
            retry_on_timeout=True,
            max_retries=3
        )
        
        # Test connection
        if _es_client.ping():
            logger.info("Elasticsearch connected successfully")
            # Initialize indices
            _initialize_indices(_es_client)
            return _es_client
        else:
            logger.error("Elasticsearch ping failed")
            _es_client = None
            return None
            
    except Exception as e:
        logger.error(f"Elasticsearch connection error: {e}")
        _es_client = None
        return None


def _initialize_indices(client):
    """Initialize Elasticsearch indices with proper mappings."""
    try:
        # Search results index
        if not client.indices.exists(index=SEARCH_RESULTS_INDEX):
            client.indices.create(
                index=SEARCH_RESULTS_INDEX,
                body={
                    "mappings": {
                        "properties": {
                            "url": {"type": "keyword"},
                            "title": {"type": "text"},
                            "snippet": {"type": "text"},
                            "source": {"type": "keyword"},
                            "document_type": {"type": "keyword"},
                            "category_ids": {"type": "keyword"},
                            "user_id": {"type": "keyword"},
                            "query": {"type": "text"},
                            "created_at": {"type": "date"},
                            "content_hash": {"type": "keyword"}
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                }
            )
            logger.info(f"Created index: {SEARCH_RESULTS_INDEX}")
        
        # Protocols index
        if not client.indices.exists(index=PROTOCOLS_INDEX):
            client.indices.create(
                index=PROTOCOLS_INDEX,
                body={
                    "mappings": {
                        "properties": {
                            "protocol_id": {"type": "keyword"},
                            "name": {"type": "text"},
                            "protocol": {"type": "text"},
                            "user_id": {"type": "keyword"},
                            "is_public": {"type": "boolean"},
                            "price": {"type": "float"},
                            "created_at": {"type": "date"}
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                }
            )
            logger.info(f"Created index: {PROTOCOLS_INDEX}")
            
    except Exception as e:
        logger.error(f"Error initializing Elasticsearch indices: {e}")


async def index_search_results(results: List[Dict], user_id: str, query: str) -> int:
    """Index search results to Elasticsearch."""
    client = get_elasticsearch_client()
    if not client:
        return 0
    
    try:
        from elasticsearch import helpers
        
        docs = []
        for result in results:
            # Create unique content hash to avoid duplicates
            content_hash = hashlib.md5(result.get("url", "").encode()).hexdigest()
            
            doc = {
                "_index": SEARCH_RESULTS_INDEX,
                "_id": content_hash,
                "_source": {
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "source": result.get("source", ""),
                    "document_type": result.get("document_type", ""),
                    "category_ids": result.get("category_ids", []),
                    "user_id": user_id,
                    "query": query,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "content_hash": content_hash
                }
            }
            docs.append(doc)
        
        if docs:
            success, failed = helpers.bulk(
                client,
                docs,
                raise_on_error=False,
                refresh="wait_for"
            )
            logger.info(f"Indexed {success} search results to Elasticsearch")
            return success
        
        return 0
        
    except Exception as e:
        logger.error(f"Error indexing to Elasticsearch: {e}")
        return 0


async def index_protocol(protocol: Dict) -> bool:
    """Index a protocol to Elasticsearch."""
    client = get_elasticsearch_client()
    if not client:
        return False
    
    try:
        doc = {
            "protocol_id": protocol.get("id", ""),
            "name": protocol.get("name", ""),
            "protocol": protocol.get("protocol", ""),
            "user_id": protocol.get("user_id", ""),
            "is_public": protocol.get("is_public", False),
            "price": protocol.get("price"),
            "created_at": protocol.get("created_at", datetime.now(timezone.utc).isoformat())
        }
        
        client.index(
            index=PROTOCOLS_INDEX,
            id=protocol.get("id"),
            body=doc,
            refresh="wait_for"
        )
        
        logger.info(f"Indexed protocol: {protocol.get('name')}")
        return True
        
    except Exception as e:
        logger.error(f"Error indexing protocol: {e}")
        return False


async def semantic_search(query: str, user_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """Perform semantic search on indexed content."""
    client = get_elasticsearch_client()
    if not client:
        return []
    
    try:
        # Build query
        must_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "snippet", "url"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            }
        ]
        
        # Add user filter if specified
        filter_clauses = []
        if user_id:
            filter_clauses.append({"term": {"user_id": user_id}})
        
        search_body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses
                }
            },
            "size": limit,
            "sort": [
                {"_score": "desc"},
                {"created_at": "desc"}
            ]
        }
        
        response = client.search(
            index=SEARCH_RESULTS_INDEX,
            body=search_body
        )
        
        results = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            source["_score"] = hit.get("_score", 0)
            results.append(source)
        
        logger.info(f"Semantic search returned {len(results)} results for '{query}'")
        return results
        
    except Exception as e:
        logger.error(f"Elasticsearch search error: {e}")
        return []


def get_elasticsearch_status() -> Dict:
    """Get Elasticsearch connection status."""
    client = get_elasticsearch_client()
    
    if not client:
        return {
            "connected": False,
            "configured": bool(ELASTICSEARCH_API_KEY),
            "message": "Elasticsearch not connected" if ELASTICSEARCH_API_KEY else "API key not configured"
        }
    
    try:
        info = client.info()
        return {
            "connected": True,
            "configured": True,
            "cluster_name": info.get("cluster_name", "unknown"),
            "version": info.get("version", {}).get("number", "unknown"),
            "indices": [SEARCH_RESULTS_INDEX, PROTOCOLS_INDEX]
        }
    except Exception as e:
        return {
            "connected": False,
            "configured": True,
            "message": str(e)
        }
