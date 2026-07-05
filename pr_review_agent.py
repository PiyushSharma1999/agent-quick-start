import anyio
import sys
from claude_agent_sdk import query, ClaudeAgentOptions

SYSTEM_PROMPT = """You are a senior engineer reviewing a pull request.

For the PR named in the user's message:
1. Use the GitHub MCP tools to fetch the PR diff + the touched files.
2. Read enough surrounding code to understand intent.
3. Produce a structured Markdown report:

   ## Summary
   One paragraph on what this PR does.

   ## Bugs
   Each with file:line and severity (high/med/low).

   ## Security
   Each with file:line, severity, and a one-line mitigation.

   ## Missing tests
   What's not covered.

   ## Verdict
   One of: approve, request_changes, comment. Justify in one sentence.

Be specific. No filler. No 'great job!' lines."""

options = ClaudeAgentOptions(
    system_prompt=SYSTEM_PROMPT,
    allowed_tools=[
        "Read",
        "Bash",
        "mcp__github__get_pull_request",
        "mcp__github__get_pull_request_files",
        "mcp__github__list_pull_request_comments",
    ],
    permission_mode="acceptEdits",
    max_turns=30,
)

async def main():
    pr = sys.argv[1] if len(sys.argv) > 1 else input("PR URL or owner/repo#N: ")
    async for msg in query(
        prompt=f"Review this PR: {pr}",
        options=options,
    ):
        print(msg)

anyio.run(main)
