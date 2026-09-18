import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.openrouter_service import OpenRouterAIService

@pytest.mark.asyncio
async def test_gemini_call_chat_completion_with_key():
    ai_svc = OpenRouterAIService(gemini_api_key="AIzaSyDummyTestKeyForUnitTesting")
    
    # Mock call_gemini to return valid response
    with patch.object(ai_svc, "call_gemini", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = '{"primary_role": "Backend Engineer", "technologies": ["Python", "Docker"]}'
        
        res = await ai_svc.call_chat_completion("Extract role from: Senior Python Engineer with Docker")
        assert res is not None
        assert "Backend Engineer" in res
        mock_gemini.assert_called_once()

@pytest.mark.asyncio
async def test_gemini_resume_analysis_integration():
    ai_svc = OpenRouterAIService(gemini_api_key="AIzaSyDummyTestKeyForUnitTesting")
    
    with patch.object(ai_svc, "call_chat_completion", new_callable=AsyncMock) as mock_comp:
        mock_comp.return_value = '{"ats_score": 92, "summary_verdict": "Outstanding profile", "strengths": ["Python", "FastAPI"], "weaknesses_and_flaws": [], "missing_metrics": [], "bullet_point_improvements": [], "actionable_recommendations": ["Apply now"]}'
        
        analysis = await ai_svc.analyze_resume("Python and FastAPI developer with 5 years experience.")
        assert analysis["ats_score"] == 92
        assert "FastAPI" in analysis["strengths"]

