import anyio
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt=(
        "You are a debugging assistant. When asked to fix a bug, "
        "read the file, propose the smallest possible fix, and "
        "explain your reasoning."
    ),
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode="default",   # asks before writes
    max_turns=10,
)

async def main():
    async for msg in query(
        prompt="Create a file called buggy.py with a Python function that has an off-by-one bug in a loop. Then fix it. Show me the diff.",
        options=options,
    ):
        print(msg)

anyio.run(main)
