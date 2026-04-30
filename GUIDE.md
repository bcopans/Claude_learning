# Claude AI — Job-Focused Learning Guide

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

Get an API key at: console.anthropic.com

---

## Learning Path

| # | Folder | Concept | Why It Matters for Jobs |
|---|--------|---------|------------------------|
| 1 | `01_basics/hello_claude.py` | First API call, message structure, token usage | Foundation — every Claude app starts here |
| 2 | `01_basics/system_prompts.py` | System prompts, multi-turn conversation | Every production AI product uses this |
| 3 | `02_tool_use/tool_use_basics.py` | Tool use / function calling | In virtually every AI eng job posting |
| 4 | `03_prompt_caching/caching_demo.py` | Prompt caching | Separates junior from senior AI engineers |
| 5 | `04_streaming/streaming_demo.py` | Streaming responses | Required for any user-facing chat UI |
| 6 | `05_structured_output/structured_output.py` | Structured JSON output | Data extraction, classification, forms |
| 7 | `06_real_project/job_application_assistant.py` | Full capstone project | Combines everything above |

---

## Core Concepts to Know for Interviews

### Models (as of mid-2025)
- **claude-opus-4-7** — most capable, best for complex reasoning
- **claude-sonnet-4-6** — best balance of speed/cost/quality (use this by default)
- **claude-haiku-4-5** — fastest and cheapest, good for high-volume simple tasks

### The Message API
```python
client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,           # required — max output tokens
    system="...",              # optional system prompt
    messages=[                 # alternating user/assistant turns
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]
)
```

### Token Costs (approximate)
- Input tokens: ~$3/M (Sonnet)
- Output tokens: ~$15/M (Sonnet)
- Cache read: ~$0.30/M (10x cheaper than input)
- Always check `message.usage` to monitor costs

### Tool Use Flow
1. You define tools as JSON schemas
2. Claude decides whether to call a tool
3. If `stop_reason == "tool_use"`, extract `tool_use` blocks
4. Execute the tool in your code
5. Send `tool_result` back in the next turn
6. Claude forms the final answer

### Prompt Caching
- Add `"cache_control": {"type": "ephemeral"}` to any content block
- Cache lasts 5 minutes (refreshed on each hit)
- Reduces cost ~90% and latency ~5x for cached content
- Best for: system prompts, large documents, few-shot examples

### Key Vocabulary for Interviews
- **Context window** — max tokens (input + output) the model sees at once
- **Temperature** — randomness (0 = deterministic, 1 = creative)
- **Top-p / top-k** — alternative sampling controls
- **Hallucination** — model confidently states false information
- **RAG** — Retrieval-Augmented Generation: fetch relevant docs before calling the LLM
- **Agent** — LLM in a loop that uses tools to complete multi-step tasks
- **Embedding** — vector representation of text, used for semantic search
- **Fine-tuning** — training a model on your specific data (not available for Claude)

---

## What AI/Claude Jobs Actually Ask For

### Junior / Mid roles
- Python proficiency
- Can you call the API and handle responses?
- Do you understand tokens, cost, and latency trade-offs?
- Have you built something with LLMs?

### Senior / Staff roles
- Architecture: when to use RAG vs fine-tuning vs prompt engineering
- Evaluation: how do you measure LLM output quality?
- Reliability: handling failures, retries, fallbacks
- Cost optimisation: caching, batching, model selection
- Agentic systems: tool orchestration, memory, planning

### Questions you should be able to answer
- "How would you prevent prompt injection attacks?"
- "How do you evaluate whether your LLM output is good?"
- "When would you choose RAG over fine-tuning?"
- "How would you reduce latency for a streaming chat product?"
- "Explain the tool use / function calling loop."

---

## Next Steps
1. Run each lesson file — reading is not enough, run the code
2. Modify the capstone (`06_real_project`) with your own resume
3. Build one small project: a chatbot, a data extractor, or a coding assistant
4. Read the Anthropic docs: docs.anthropic.com
5. Follow Anthropic's model release blog for latest capabilities
