"""
Legacy import wrapper for OpenRouter AIService.
Maintains full backward compatibility with existing cogs and service imports.
"""
from services.openrouter_service import (
    OpenRouterAIService,
    GeminiResumeService,
    gemini_service,
    openrouter_service
)

__all__ = [
    "OpenRouterAIService",
    "GeminiResumeService",
    "gemini_service",
    "openrouter_service"
]
