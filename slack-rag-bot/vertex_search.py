import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from google.cloud import discoveryengine_v1alpha as discoveryengine
import google.auth


@dataclass
class SearchResult:
    title: str
    snippet: str
    source_uri: str
    confidence_score: float
    metadata: Dict[str, Any] = None


class VertexSearchClient:
    def __init__(self, project_id: str, location: str, data_store_id: str, app_id: str):
        self.project_id = project_id
        self.location = location
        self.data_store_id = data_store_id
        self.app_id = app_id
        
        # Initialize the client
        self.client = discoveryengine.SearchServiceClient()
        
        # Build the serving config path
        self.serving_config = (
            f"projects/{project_id}/locations/{location}"
            f"/dataStores/{data_store_id}/servingConfigs/default_config"
        )
        
        # Alternative path format for apps
        self.app_serving_config = (
            f"projects/{project_id}/locations/{location}"
            f"/collections/default_collection/engines/{app_id}/servingConfigs/default_config"
        )
        
        logging.info(f"Initialized VertexSearchClient for project: {project_id}")
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        use_grounded_generation: bool = True,
        filter_expr: Optional[str] = None
    ) -> List[SearchResult]:
        try:
            # Prepare the search request
            request = discoveryengine.SearchRequest(
                serving_config=self.serving_config,
                query=query,
                page_size=max_results,
            )
            
            # Add content search spec for extractive answers
            if use_grounded_generation:
                request.content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True,
                        max_snippet_count=3,
                    ),
                    summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                        summary_result_count=5,
                        include_citations=True,
                    ),
                )
            
            # Add filter if provided
            if filter_expr:
                request.filter = filter_expr
            
            logging.info(f"Executing search query: '{query}' with max_results: {max_results}")
            
            # Execute the search
            response = self.client.search(request=request)
            
            # Convert results to list to avoid iterator issues
            results_list = list(response.results) if response.results else []
            logging.info(f"Search response received. Results count: {len(results_list)}")
            
            # Update response.results with the list
            response.results = results_list
            
            # Process results
            results = []
            if not response.results:
                logging.warning("No results returned from search")
                return results
                
            for result in response.results:
                document = result.document
                
                try:
                    # Extract basic info
                    title = self._extract_title(document)
                    snippet = self._extract_snippet(document)
                    
                    source_uri = ""
                    if hasattr(document, 'derived_struct_data') and document.derived_struct_data:
                        source_uri = document.derived_struct_data.get("link", "")
                    
                    # Calculate confidence score (simplified)
                    confidence_score = self._calculate_confidence(result)
                    
                    # Extract metadata
                    metadata = self._extract_metadata(document)
                except Exception as e:
                    logging.error(f"Error processing document: {str(e)}")
                    continue
                
                search_result = SearchResult(
                    title=title,
                    snippet=snippet,
                    source_uri=source_uri,
                    confidence_score=confidence_score,
                    metadata=metadata
                )
                results.append(search_result)
            
            logging.info(f"Retrieved {len(results)} search results")
            return results
            
        except Exception as e:
            logging.error(f"Error during search: {str(e)}")
            # Try alternative serving config path
            try:
                request.serving_config = self.app_serving_config
                response = self.client.search(request=request)
                
                results = []
                for result in response.results:
                    document = result.document
                    
                    title = self._extract_title(document)
                    snippet = self._extract_snippet(document)
                    source_uri = ""
                    if hasattr(document, 'derived_struct_data') and document.derived_struct_data:
                        source_uri = document.derived_struct_data.get("link", "")
                    confidence_score = self._calculate_confidence(result)
                    metadata = self._extract_metadata(document)
                    
                    search_result = SearchResult(
                        title=title,
                        snippet=snippet,
                        source_uri=source_uri,
                        confidence_score=confidence_score,
                        metadata=metadata
                    )
                    results.append(search_result)
                
                logging.info(f"Retrieved {len(results)} search results using app config")
                return results
                
            except Exception as fallback_e:
                logging.error(f"Fallback search also failed: {str(fallback_e)}")
                raise e
    
    def _extract_title(self, document) -> str:
        struct_data = document.struct_data if hasattr(document, 'struct_data') and document.struct_data else {}
        derived_data = document.derived_struct_data if hasattr(document, 'derived_struct_data') and document.derived_struct_data else {}
        
        # Try derived_data first (usually has cleaner title)
        for field in ["title", "name", "filename", "document_title"]:
            if derived_data and field in derived_data and derived_data[field]:
                return str(derived_data[field])
        
        # Fallback to struct_data
        for field in ["title", "name", "filename", "document_title"]:
            if struct_data and field in struct_data and struct_data[field]:
                return str(struct_data[field])
        
        # Fallback to document ID or URI
        if hasattr(document, 'id') and document.id:
            return document.id
        
        return "Untitled Document"
    
    def _extract_snippet(self, document) -> str:
        struct_data = document.struct_data if hasattr(document, 'struct_data') and document.struct_data else {}
        derived_data = document.derived_struct_data if hasattr(document, 'derived_struct_data') and document.derived_struct_data else {}
        
        # Try extracting from snippets array first (common in Vertex AI Search)
        if derived_data and "snippets" in derived_data and derived_data["snippets"]:
            snippets = derived_data["snippets"]
            try:
                # Convert to list if it's a protobuf RepeatedComposite
                snippets_list = list(snippets)
                
                if len(snippets_list) > 0:
                    # Take the first snippet
                    first_snippet = snippets_list[0]
                    
                    # Handle MapComposite object with bracket notation
                    if "snippet" in first_snippet:
                        content = str(first_snippet["snippet"])
                        if content and content.strip():
                            return content[:500] + "..." if len(content) > 500 else content
                    
                    # Also try dict-like access
                    if isinstance(first_snippet, dict) and "snippet" in first_snippet:
                        content = str(first_snippet["snippet"])
                        return content[:500] + "..." if len(content) > 500 else content
                    elif hasattr(first_snippet, 'snippet'):
                        # Handle protobuf object
                        content = str(first_snippet.snippet)
                        return content[:500] + "..." if len(content) > 500 else content
                    elif isinstance(first_snippet, dict):
                        # Try other possible keys
                        for key in ["content", "text", "extractive_content"]:
                            if key in first_snippet and first_snippet[key]:
                                content = str(first_snippet[key])
                                return content[:500] + "..." if len(content) > 500 else content
                    elif isinstance(first_snippet, str):
                        content = str(first_snippet)
                        return content[:500] + "..." if len(content) > 500 else content
                    else:
                        # Try to extract any string attribute
                        content = str(first_snippet)
                        if content and content != str(type(first_snippet)):
                            return content[:500] + "..." if len(content) > 500 else content
            except Exception as e:
                logging.warning(f"Error processing snippets: {e}")
                pass
        
        # Try various other content fields
        for field in ["content", "snippet", "text", "body", "extractive_answers"]:
            if struct_data and field in struct_data and struct_data[field]:
                content = str(struct_data[field])
                return content[:500] + "..." if len(content) > 500 else content
            if derived_data and field in derived_data and derived_data[field]:
                content = str(derived_data[field])
                return content[:500] + "..." if len(content) > 500 else content
        
        return "No preview available"
    
    def _calculate_confidence(self, result) -> float:
        # Simple confidence scoring based on available data
        # In a real implementation, you might use more sophisticated scoring
        base_score = 0.5
        
        # Boost score if we have good metadata
        if hasattr(result, 'document') and result.document.struct_data:
            base_score += 0.2
        
        # You could add more sophisticated scoring here
        return min(base_score, 1.0)
    
    def _extract_metadata(self, document) -> Dict[str, Any]:
        metadata = {}
        
        if hasattr(document, 'struct_data') and document.struct_data:
            try:
                struct_data = dict(document.struct_data)
                # Filter out content fields to keep metadata clean
                content_fields = {"content", "text", "body", "snippet"}
                metadata.update({
                    k: v for k, v in struct_data.items() 
                    if k not in content_fields
                })
            except (TypeError, ValueError) as e:
                logging.warning(f"Could not extract metadata from struct_data: {e}")
        
        return metadata
    
    def test_connection(self) -> bool:
        try:
            # Simple test query to verify connection
            test_query = "test"
            request = discoveryengine.SearchRequest(
                serving_config=self.serving_config,
                query=test_query,
                page_size=1,
            )
            
            response = self.client.search(request=request)
            logging.info("Connection test successful")
            return True
            
        except Exception as e:
            logging.error(f"Connection test failed: {str(e)}")
            try:
                # Try alternative config
                request.serving_config = self.app_serving_config
                response = self.client.search(request=request)
                logging.info("Connection test successful with app config")
                return True
            except Exception as fallback_e:
                logging.error(f"Fallback connection test also failed: {str(fallback_e)}")
                return False