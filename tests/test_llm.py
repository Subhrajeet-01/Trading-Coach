import pytest
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.pattern_engine import Signal
from app.services.llm_service import stream_coaching

@pytest.mark.asyncio
async def test_stream_coaching():
    """
    Integration test for the LLM streaming service.
    """
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not found in environment. Skipping LLM integration test.")

    # Mocking some input data for the LLM
    mock_signals = [
        Signal(
            pathology="revenge_trading",
            confidence=0.85,
            evidence=[{"tradeId": "t102", "sessionId": "s001", "reason": "Immediate re-entry after loss on TSLA"}]
        )
    ]
    
    mock_context = {
        "sessions": [
            {"session_id": "s001", "summary": "Chased losses on tech stocks, displaying emotional attachment."}
        ]
    }
    
    chunks_received = 0
    try:
        # Iterate over the async generator
        async for chunk in stream_coaching(mock_signals, mock_context):
            assert isinstance(chunk, str)
            chunks_received += 1
            
        assert chunks_received > 0, "No chunks were received from the streaming service"
        
    except Exception as e:
        pytest.fail(f"LLM Streaming failed: {e}")
