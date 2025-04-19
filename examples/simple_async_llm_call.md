
# Simple Async LLM Call Example

This example demonstrates how to make asynchronous calls to the LLM service in GitRecap.

## Prerequisites

1. Ensure you have the environment variables set (see [Configuration Guide](${AiCore_GitHub:-.}/config/index.md))
2. Install required dependencies:
```bash
pip install -r ${AiCore_GitHub:-.}/requirements.txt
```

## Example Code

```python
import asyncio
from fastapi import FastAPI
from git_recap.services.llm_service import LLMService

app = FastAPI()
llm_service = LLMService()

async def get_llm_response(prompt: str) -> str:
    """Make an async call to the LLM service."""
    try:
        response = await llm_service.generate_async(prompt)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

async def main():
    prompt = "Summarize the git activity for the last week"
    response = await get_llm_response(prompt)
    print(f"LLM Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Components

1. **LLM Service**: 
   - Uses the [`LLMService`](${AiCore_GitHub:-.}/app/api/services/llm_service.py) from the API
   - Handles authentication and connection to the LLM provider

2. **Async Pattern**:
   - Uses Python's `asyncio` for non-blocking calls
   - Follows FastAPI's async conventions

3. **Error Handling**:
   - Basic exception handling included
   - For production use, implement proper error handling (see [Observability Guide](${AiCore_GitHub:-.}/observability/index.md))

## Integration Points

This example connects with:
- [FastAPI backend](${AiCore_GitHub:-.}/app/api/main.py)
- [LLM service](${AiCore_GitHub:-.}/app/api/services/llm_service.py)
- [Configuration system](${AiCore_GitHub:-.}/config/index.md)

## Running the Example

1. Save the code to a file (e.g., `llm_example.py`)
2. Run with:
```bash
python llm_example.py
```

## Next Steps

For more advanced usage:
- See [FastAPI integration examples](${AiCore_GitHub:-.}/examples/fastapi)
- Review [prompt engineering guidelines](${AiCore_GitHub:-.}/app/api/services/prompts.py)
- Check the [API documentation](${AiCore_GitHub:-.}/docs/backend.md) for additional endpoints