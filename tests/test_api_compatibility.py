"""
Tests for API endpoint backward compatibility.

These tests verify that the API endpoints maintain backward compatibility
with existing client request formats and response structures.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 9.1
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np

from app.main import app


class TestAPIBackwardCompatibility:
    """Test suite for API backward compatibility."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_recommender(self):
        """Create a mock recommender with sample recommendations."""
        mock = MagicMock()
        
        # Mock recommend method to return sample recommendations
        mock.recommend.return_value = [
            {
                "id": 1,
                "name": "María García",
                "score": 0.8945,
                "top_illustration_url": "https://example.com/image1.jpg",
                "num_illustrations": 12,
                "aggregation_strategy": "max"
            },
            {
                "id": 5,
                "name": "Ana Martínez",
                "score": 0.8723,
                "top_illustration_url": "https://example.com/image5.jpg",
                "num_illustrations": 8,
                "aggregation_strategy": "max"
            },
            {
                "id": 12,
                "name": "Luis Fernández",
                "score": 0.8456,
                "top_illustration_url": "https://example.com/image12.jpg",
                "num_illustrations": 5,
                "aggregation_strategy": "max"
            }
        ]
        
        # Mock artists list
        mock.artists = [
            {
                "id": 1,
                "name": "María García",
                "description": "Ilustrador: María García. Especialista en ilustración digital...",
                "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
            },
            {
                "id": 5,
                "name": "Ana Martínez",
                "description": "Ilustrador: Ana Martínez. Experta en ilustración infantil...",
                "image_urls": ["https://example.com/image5.jpg"]
            }
        ]
        
        return mock
    
    def test_post_recommend_accepts_correct_request_format(self, client, mock_recommender):
        """
        Test that POST /recommend accepts the same request format as before.
        
        Validates: Requirements 6.1
        """
        # Patch the global recommender
        with patch('app.main.recommender', mock_recommender):
            # Request format from API_EXAMPLES.md
            request_data = {
                "titulo": "Ilustración para libro infantil",
                "descripcion": "Necesito ilustraciones coloridas y amigables para un libro de cuentos",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Experiencia en ilustración infantil, estilo cartoon",
                "top_k": 3
            }
            
            response = client.post("/recommend", json=request_data)
            
            # Should accept the request successfully
            assert response.status_code == 200
            
            # Verify recommender was called
            assert mock_recommender.recommend.called
    
    def test_post_recommend_accepts_optional_image_url(self, client, mock_recommender):
        """
        Test that POST /recommend accepts optional image_url field.
        
        Validates: Requirements 6.1
        """
        with patch('app.main.recommender', mock_recommender):
            request_data = {
                "titulo": "Ilustración para libro infantil",
                "descripcion": "Necesito ilustraciones coloridas",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Experiencia en ilustración infantil",
                "top_k": 5,
                "image_url": "https://example.com/reference-style.jpg"
            }
            
            response = client.post("/recommend", json=request_data)
            
            # Should accept the request with image_url
            assert response.status_code == 200
    
    def test_post_recommend_returns_correct_response_structure(self, client, mock_recommender):
        """
        Test that POST /recommend returns the correct response structure.
        
        Validates: Requirements 6.2, 6.3
        """
        with patch('app.main.recommender', mock_recommender):
            request_data = {
                "titulo": "Test Project",
                "descripcion": "Test description",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Test requirements",
                "top_k": 3
            }
            
            response = client.post("/recommend", json=request_data)
            
            assert response.status_code == 200
            
            data = response.json()
            
            # Should have recommended_artists key
            assert "recommended_artists" in data
            assert isinstance(data["recommended_artists"], list)
    
    def test_post_recommend_response_contains_required_fields(self, client, mock_recommender):
        """
        Test that each recommended artist contains required fields.
        
        Validates: Requirements 6.3
        """
        with patch('app.main.recommender', mock_recommender):
            request_data = {
                "titulo": "Test Project",
                "descripcion": "Test description",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Test requirements",
                "top_k": 3
            }
            
            response = client.post("/recommend", json=request_data)
            data = response.json()
            
            artists = data["recommended_artists"]
            
            # Each artist should have required fields (from API_EXAMPLES.md)
            for artist in artists:
                # Core required fields
                assert "id" in artist
                assert "name" in artist
                assert "score" in artist
                
                # Verify field types
                assert isinstance(artist["id"], int)
                assert isinstance(artist["name"], str)
                assert isinstance(artist["score"], (int, float))
    
    def test_post_recommend_response_contains_backward_compatible_fields(self, client, mock_recommender):
        """
        Test that response contains backward compatible fields from API examples.
        
        This ensures existing clients continue to work without changes.
        
        Validates: Requirements 6.3, 6.4
        """
        # Update mock to return full artist data
        mock_recommender.recommend.return_value = [
            {
                "id": 1,
                "name": "María García",
                "score": 0.8945,
                "description": "Ilustrador: María García. Especialista en ilustración digital...",
                "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
                "image_path": "https://example.com/image1.jpg",
                "top_illustration_url": "https://example.com/image1.jpg",
                "num_illustrations": 12,
                "aggregation_strategy": "max"
            }
        ]
        
        with patch('app.main.recommender', mock_recommender):
            request_data = {
                "titulo": "Test Project",
                "descripcion": "Test description",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Test requirements",
                "top_k": 3
            }
            
            response = client.post("/recommend", json=request_data)
            data = response.json()
            
            artists = data["recommended_artists"]
            
            # Verify backward compatible fields are present
            for artist in artists:
                # Fields from API_EXAMPLES.md that existing clients expect
                assert "description" in artist, "Missing 'description' field for backward compatibility"
                assert "image_urls" in artist, "Missing 'image_urls' field for backward compatibility"
                assert "image_path" in artist, "Missing 'image_path' field for backward compatibility"
                
                # Verify types
                assert isinstance(artist["description"], str)
                assert isinstance(artist["image_urls"], list)
                assert isinstance(artist["image_path"], (str, type(None)))
    
    def test_post_recommend_score_in_valid_range(self, client, mock_recommender):
        """
        Test that scores are in the valid range [0, 1].
        
        Validates: Requirements 6.5
        """
        with patch('app.main.recommender', mock_recommender):
            request_data = {
                "titulo": "Test Project",
                "descripcion": "Test description",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Test requirements",
                "top_k": 3
            }
            
            response = client.post("/recommend", json=request_data)
            data = response.json()
            
            artists = data["recommended_artists"]
            
            # All scores should be in [0, 1] range
            for artist in artists:
                score = artist["score"]
                assert 0.0 <= score <= 1.0, f"Score {score} is out of range [0, 1]"
    
    def test_get_process_all_returns_correct_structure(self, client, mock_recommender):
        """
        Test that GET /recommendations/process_all returns correct structure.
        
        Validates: Requirements 6.2
        """
        # Mock project service client
        mock_projects = [
            {
                "id": 1,
                "titulo": "Proyecto 1",
                "descripcion": "Descripción 1",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Requisitos 1"
            },
            {
                "id": 2,
                "titulo": "Proyecto 2",
                "descripcion": "Descripción 2",
                "modalidadProyecto": "PRESENCIAL",
                "contratoProyecto": "TIEMPO_COMPLETO",
                "especialidadProyecto": "CONCEPT_ART",
                "requisitos": "Requisitos 2"
            }
        ]
        
        with patch('app.main.recommender', mock_recommender):
            with patch('app.main.project_service_client') as mock_project_client:
                mock_project_client.get_all_projects.return_value = mock_projects
                mock_project_client.transform_project_to_internal_format.side_effect = lambda x: x
                mock_project_client.build_semantic_query.return_value = "Test query"
                
                response = client.get("/recommendations/process_all")
                
                assert response.status_code == 200
                
                data = response.json()
                
                # Should have batch_results key
                assert "batch_results" in data
                assert isinstance(data["batch_results"], list)
    
    def test_get_process_all_batch_result_structure(self, client, mock_recommender):
        """
        Test that each batch result has the correct structure.
        
        Validates: Requirements 6.2, 6.3
        """
        mock_projects = [
            {
                "id": 1,
                "titulo": "Proyecto 1",
                "descripcion": "Descripción 1",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Requisitos 1"
            }
        ]
        
        with patch('app.main.recommender', mock_recommender):
            with patch('app.main.project_service_client') as mock_project_client:
                mock_project_client.get_all_projects.return_value = mock_projects
                mock_project_client.transform_project_to_internal_format.side_effect = lambda x: x
                mock_project_client.build_semantic_query.return_value = "Test query"
                
                response = client.get("/recommendations/process_all")
                data = response.json()
                
                batch_results = data["batch_results"]
                
                # Each batch result should have required fields
                for result in batch_results:
                    assert "project_id" in result
                    assert "project_titulo" in result
                    assert "recommended_artists" in result
                    
                    # Verify types
                    assert isinstance(result["project_id"], int)
                    assert isinstance(result["project_titulo"], str)
                    assert isinstance(result["recommended_artists"], list)
    
    def test_api_handles_errors_gracefully(self, client, mock_recommender):
        """
        Test that API handles errors gracefully without breaking.
        
        Validates: Requirements 6.4, 9.1
        """
        # Make recommender raise an exception
        mock_recommender.recommend.side_effect = Exception("Test error")
        
        with patch('app.main.recommender', mock_recommender):
            request_data = {
                "titulo": "Test Project",
                "descripcion": "Test description",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Test requirements",
                "top_k": 3
            }
            
            response = client.post("/recommend", json=request_data)
            
            # Should return error status code
            assert response.status_code == 500
            
            # Should have error detail
            data = response.json()
            assert "detail" in data
    
    def test_invalid_enum_values_rejected(self, client):
        """
        Test that invalid enum values are rejected with proper error.
        
        Validates: Requirements 6.1
        """
        request_data = {
            "titulo": "Test Project",
            "descripcion": "Test description",
            "modalidadProyecto": "INVALID_MODE",  # Invalid enum value
            "contratoProyecto": "FREELANCE",
            "especialidadProyecto": "ILUSTRACION_DIGITAL",
            "requisitos": "Test requirements",
            "top_k": 3
        }
        
        response = client.post("/recommend", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_missing_required_fields_rejected(self, client):
        """
        Test that requests with missing required fields are rejected.
        
        Validates: Requirements 6.1
        """
        request_data = {
            "titulo": "Test Project",
            # Missing descripcion
            "modalidadProyecto": "REMOTO",
            "contratoProyecto": "FREELANCE",
            "especialidadProyecto": "ILUSTRACION_DIGITAL",
            "requisitos": "Test requirements",
            "top_k": 3
        }
        
        response = client.post("/recommend", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_default_top_k_value(self, client, mock_recommender):
        """
        Test that top_k has a default value when not provided.
        
        Validates: Requirements 6.1
        """
        with patch('app.main.recommender', mock_recommender):
            request_data = {
                "titulo": "Test Project",
                "descripcion": "Test description",
                "modalidadProyecto": "REMOTO",
                "contratoProyecto": "FREELANCE",
                "especialidadProyecto": "ILUSTRACION_DIGITAL",
                "requisitos": "Test requirements"
                # top_k not provided - should use default
            }
            
            response = client.post("/recommend", json=request_data)
            
            # Should accept request with default top_k
            assert response.status_code == 200
            
            # Verify recommender was called with default top_k=3
            call_args = mock_recommender.recommend.call_args
            assert call_args[1]["top_k"] == 3
