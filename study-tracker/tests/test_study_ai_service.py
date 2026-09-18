import pytest
from unittest.mock import AsyncMock, patch
from services.ai_service import StudyTrackerAIService, ai_service
from services.roast_service import roast_service

@pytest.mark.asyncio
async def test_study_tracker_ai_roast():
    st_ai = StudyTrackerAIService(gemini_api_key="AIzaSyDummyTestKeyForUnitTesting")
    
    with patch.object(st_ai, "call_chat_completion", new_callable=AsyncMock) as mock_comp:
        mock_comp.return_value = "Your streak is on life support! Log a topic before your IDE uninstalls itself."
        
        roast = await st_ai.generate_ai_roast("Alex", streak_count=3, recent_topics=["Dynamic Programming"])
        assert roast is not None
        assert "streak" in roast.lower() or "ide" in roast.lower()

@pytest.mark.asyncio
async def test_roast_service_dynamic_roast_fallback():
    # Test that get_dynamic_roast falls back cleanly if no AI key or AI fails
    roast = await roast_service.get_dynamic_roast(username="Sarah", streak_count=4)
    assert "Sarah" in roast
    assert len(roast) > 20
