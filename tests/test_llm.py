import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.pattern_engine import Signal
from app.services.llm_service import stream_coaching

async def main():
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️ Warning: GROQ_API_KEY is not found in the environment variables.")
        print("Make sure you add it to your .env file!")
        return

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
    
    print("🚀 Sending prompt to Groq (streaming response)...\n")
    print("-" * 50)
    
    try:
        # We iterate over the async generator
        async for chunk in stream_coaching(mock_signals, mock_context):
            print(chunk, end='', flush=True)
            
        print("\n\n✅ Groq streaming finished successfully.")
    except Exception as e:
        print(f"\n\n❌ Error during streaming: {e}")
        print("\nCheck if your GROQ_API_KEY is correct!")

if __name__ == "__main__":
    asyncio.run(main())
