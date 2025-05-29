"""
Base repository class for Firestore operations
"""
from typing import Dict, Any, Optional, List
from google.cloud import firestore
from google.api_core import exceptions
import logging
from datetime import datetime

from src.core.firestore import get_db

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base class for Firestore repositories"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.db = get_db()
        self.collection = self.db.collection(collection_name)
    
    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None
    
    async def create(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Create new document
        
        Args:
            doc_id: Document ID
            data: Document data
            
        Returns:
            True if successful
        """
        try:
            # Add timestamps
            data['created_at'] = firestore.SERVER_TIMESTAMP
            data['last_updated'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.collection.document(doc_id)
            doc_ref.set(data)
            return True
            
        except Exception as e:
            logger.error(f"Error creating document {doc_id}: {e}")
            return False
    
    async def update(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Update existing document
        
        Args:
            doc_id: Document ID
            data: Fields to update
            
        Returns:
            True if successful
        """
        try:
            # Add update timestamp
            data['last_updated'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.collection.document(doc_id)
            doc_ref.update(data)
            return True
            
        except exceptions.NotFound:
            logger.warning(f"Document {doc_id} not found for update")
            return False
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False
    
    async def delete(self, doc_id: str) -> bool:
        """
        Delete document
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc_ref.delete()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    async def query(
        self,
        filters: List[tuple] = None,
        order_by: str = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents
        
        Args:
            filters: List of (field, operator, value) tuples
            order_by: Field to order by
            limit: Maximum number of results
            
        Returns:
            List of documents
        """
        try:
            query = self.collection
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query
            docs = query.get()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            return []