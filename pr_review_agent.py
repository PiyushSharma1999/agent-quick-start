import anyio
import sys
from claude_agent_sdk import query, ClaudeAgentOptions

SYSTEM_PROMPT = """You are a senior engineer reviewing a pull request.

1. Use the GitHub MCP tools to fetch the PR diff + touched files.
2. Spawn a sub-agent using the Task tool for the security review:
   - Sub-agent system prompt: read the file security_prompt.md
   - Sub-agent prompt: paste the full diff
   - Wait for the JSON response.
3. Run run_project_lint on each touched file.
4. Synthesize a final Markdown report with sections:
   ## Summary
   ## Bugs
   ## Security  (use the sub-agent's findings, sort by severity)
   ## Lint
   ## Missing tests
   ## Verdict

Be specific. No filler."""

@tool(
    "run_project_lint",
    "Runs the project linter and returns structured findings",
    {"path": str},
)
async def run_project_lint(args):
    """Run ruff (Python) or eslint (JS) on the given path."""
    path = args["path"]
    try:
        # Try ruff first (Python projects), then eslint
        result = subprocess.run(
            ["ruff", "check", path, "--output-format=json"],
            capture_output=True, text=True, timeout=60,
        )
        findings = json.loads(result.stdout) if result.stdout else []
    except (FileNotFoundError, json.JSONDecodeError):
        result = subprocess.run(
            ["npx", "eslint", path, "--format=json"],
            capture_output=True, text=True, timeout=60,
        )
        findings = json.loads(result.stdout) if result.stdout else []

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({"findings": findings[:50]}, indent=2),
        }]
    }

lint_server = create_sdk_mcp_server(
    name="lint", version="1.0.0", tools=[run_project_lint],
)

options = ClaudeAgentOptions(
    system_prompt=SYSTEM_PROMPT + (
        "\n\nWhen reviewing, also call run_project_lint on each touched "
        "file and include the linter findings under a '## Lint' section."
    ),
    mcp_servers={"lint": lint_server},
    allowed_tools=[
        "Read", "Bash",
        "mcp__github__get_pull_request",
        "mcp__github__get_pull_request_files",
        "mcp__lint__run_project_lint",
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
