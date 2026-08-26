"""
Agent Core — Boucle agentique ReAct (Reason + Act).
V2: Supporte 4 outils (list_dir, read_file, copy_file, write_file).
Parse les réponses du LLM, exécute les outils, reboucle jusqu'à une réponse finale.
"""

import os
import re
import time
from llm import get_auth_context, LLMChat
from agent_tools import TOOLS_DESCRIPTION, TOOL_FUNCTIONS
from path_guard import PathGuard, ALLOWED_ROOT_DIR

# ─── Config ─────────────────────────────────────────────────

MODELS = ["gpt-oss-120b", "mistral-medium-3.5-ITG", "gemma-4-26b"]
MAX_ITERATIONS = 10

SYSTEM_PROMPT = f"""You are an intelligent file management and analysis assistant. You help users navigate, read, analyze, transform, and write files within a secured directory.

WORKING DIRECTORY: {ALLOWED_ROOT_DIR}
You can ONLY access files and folders inside this directory.

{TOOLS_DESCRIPTION}

━━━ YOUR CAPABILITIES ━━━

You are a powerful language model. When you read a file, you DO NOT just relay its content.
You can and SHOULD use your intelligence to:
- SUMMARIZE: Condense a long document into key points.
- ANALYZE: Identify patterns, issues, risks, or insights in file content.
- TRANSFORM: Reformat content (e.g., turn prose into a table, extract data into CSV/Excel).
- TRANSLATE: Convert content between languages.
- COMPARE: Read multiple files and highlight differences or similarities.
- GENERATE: Write original content based on what you've read (reports, summaries, emails, memos).
- EXTRACT: Pull specific data points (names, dates, numbers, IOCs) from unstructured text.

When the user asks you to "summarize a file and write it to a Word document", you MUST:
1. Read the file with read_file.
2. Use YOUR OWN intelligence to produce a rich, detailed summary.
3. Write that summary to the target file with write_file.

You are NOT a dumb file copier. You ARE the brain. Act like it.

━━━ RESPONSE FORMAT ━━━

When you need to use a tool, respond with EXACTLY this format:
THOUGHT: <your reasoning about what to do next>
ACTION: <tool_name> | <arguments>

For tools with multiple arguments, separate them with |
  Example: ACTION: copy_file | source.txt | destination.txt
  Example: ACTION: write_file | notes.txt | Content to write here

When you have enough information to answer the user, respond with:
THOUGHT: <your reasoning>
ANSWER: <your complete response to the user>

━━━ RULES ━━━
1. Use ONE tool per turn. Wait for the OBSERVATION before calling another.
2. Paths are RELATIVE to the working directory. Use "." for the root.
3. NEVER invent or guess file contents — only report what tools return.
4. If a tool returns an error, explain it clearly to the user.
5. Answer in the SAME LANGUAGE as the user (French if they write French, etc.).
6. Be concise but informative.
7. For write_file, include the FULL content to write after the path. When writing summaries, reports, or analysis, produce RICH and DETAILED content — never just a title or placeholder.
8. You CANNOT write or copy to protected extensions (.py, .bat, .ps1, .sh, .exe, .dll).
9. When writing .xlsx files, output the raw CSV data as the content.
10. NEVER tell the user you cannot handle .xlsx or .docx. You CAN handle them natively. Do not mention CSV conversions to the user.
11. NEVER say you lack summarization, analysis, or generation capabilities. You ARE the intelligence. Use it.
"""


# ─── Main agent loop ────────────────────────────────────────

def run_agent(
    user_message: str,
    conversation_history: list[dict],
    auth_context,
) -> tuple[str, list[dict]]:
    """
    Execute the ReAct agent loop.

    Args:
        user_message: The user's current question.
        conversation_history: Previous messages [{"role": ..., "content": ...}].
        auth_context: Authentication context from get_auth_context().

    Returns:
        (final_answer, debug_logs)
    """
    guard = PathGuard()
    debug_logs = []

    # Build the full prompt with history
    prompt = SYSTEM_PROMPT + "\n"
    for msg in conversation_history:
        role = msg["role"].upper()
        prompt += f"{role}: {msg['content']}\n"
    prompt += f"USER: {user_message}\n"

    for iteration in range(1, MAX_ITERATIONS + 1):
        step = {"iteration": iteration, "events": []}

        # ── Call LLM ──
        t0 = time.time()
        raw_response, model_used = _call_llm(prompt, auth_context)
        elapsed = time.time() - t0

        step["model"] = model_used
        step["duration"] = f"{elapsed:.1f}s"
        step["events"].append(("🤖 RAW", raw_response[:500]))

        # ── Parse response ──
        thought = _extract(r"THOUGHT:\s*(.+?)(?=ACTION:|ANSWER:|$)", raw_response)
        action  = _extract(r"ACTION:\s*(.+?)(?:\n|$)", raw_response)
        answer  = _extract(r"ANSWER:\s*(.+)", raw_response, dotall=True)

        if thought:
            step["events"].append(("🧠 THOUGHT", thought.strip()))

        # ── Case A: Final answer ──
        if answer:
            step["events"].append(("✅ ANSWER", answer.strip()[:300]))
            debug_logs.append(step)
            return answer.strip(), debug_logs

        # ── Case B: Tool call ──
        if action:
            # Parse tool name and arguments
            # For single-arg tools: "tool_name | arg"
            # For multi-arg tools:  "tool_name | arg1 | arg2"
            parts = action.split("|", 1)
            tool_name = parts[0].strip().lower()
            tool_arg = parts[1].strip() if len(parts) > 1 else "."

            step["events"].append(("🔧 ACTION", f"{tool_name}( {tool_arg} )"))

            if tool_name in TOOL_FUNCTIONS:
                # Execute tool (PathGuard validates inside)
                result = TOOL_FUNCTIONS[tool_name](tool_arg, guard)

                # Capture guard logs
                for gl in guard.get_logs():
                    step["events"].append(
                        (f"🛡️ {gl['verdict']}", gl["reason"])
                    )
                guard.clear_logs()

                # Format observation for LLM
                if result["success"]:
                    obs = _format_observation(tool_name, result)
                    preview = obs[:250] + ("..." if len(obs) > 250 else "")
                    step["events"].append(("📄 RESULT", preview))
                else:
                    obs = f"ERROR: {result['error']}"
                    step["events"].append(("❌ ERROR", obs))
            else:
                obs = (
                    f"ERROR: Unknown tool '{tool_name}'. "
                    f"Available tools: list_dir, read_file, copy_file, write_file, move_file, search_in_files, delete_file, create_dir, append_to_file."
                )
                step["events"].append(("❌ ERROR", obs))

            # Feed observation back to LLM
            prompt += f"ASSISTANT: {raw_response}\nOBSERVATION: {obs}\n"

        else:
            # No ACTION and no ANSWER — LLM didn't follow format
            step["events"].append(
                ("⚠️ FORMAT", "Le LLM n'a pas suivi le format requis — réponse brute utilisée.")
            )
            debug_logs.append(step)
            return raw_response.strip(), debug_logs

        debug_logs.append(step)

    # Safety: max iterations reached
    return (
        "⚠️ Nombre maximum d'itérations atteint. Essayez une question plus simple.",
        debug_logs,
    )


# ─── Observation formatter ───────────────────────────────────

def _sanitize_path(full_path: str) -> str:
    """Strip root directory from path to avoid leaking internal structure to LLM."""
    root = PathGuard().root_dir
    if full_path.startswith(root):
        relative = full_path[len(root):]
        return relative.lstrip(os.sep) or "."
    return full_path

def _format_observation(tool_name: str, result: dict) -> str:
    """Format a successful tool result into a text observation for the LLM."""
    if tool_name == "list_dir":
        return (
            f"Directory: {_sanitize_path(result['path'])}\n"
            f"{result['count']} items found:\n"
            + "\n".join(result["entries"])
        )

    elif tool_name == "read_file":
        trunc_tag = " [TRUNCATED]" if result.get("truncated") else ""
        # Wrap content in unique delimiters to prevent prompt injection
        # (file content could contain "ANSWER:" or "ACTION:" strings)
        return (
            f"File: {_sanitize_path(result['path'])}{trunc_tag}\n"
            f"<<<FILE_CONTENT_START>>>\n{result['content']}\n<<<FILE_CONTENT_END>>>"
        )

    elif tool_name == "copy_file":
        msg = f"SUCCESS: {result['message']}\nSource: {_sanitize_path(result['source'])}\nDestination: {_sanitize_path(result['destination'])}"
        if result.get("backup"):
            msg += f"\nBackup created."
        return msg

    elif tool_name == "write_file":
        msg = f"SUCCESS: {result['message']}\nPath: {_sanitize_path(result['path'])}\nChars written: {result['chars_written']}"
        if result.get("backup"):
            msg += f"\nBackup created."
        return msg

    elif tool_name == "move_file":
        msg = f"SUCCESS: {result['message']}\nSource: {_sanitize_path(result['source'])}\nDestination: {_sanitize_path(result['destination'])}"
        if result.get("backup"):
            msg += f"\nBackup created."
        return msg

    elif tool_name == "search_in_files":
        return (
            f"Found {result['count']} matches for '{result['pattern']}':\n"
            + "\n".join(result["results"])
        )

    elif tool_name == "delete_file":
        return f"SUCCESS: {result['message']}"

    elif tool_name == "create_dir":
        return f"SUCCESS: {result['message']}\nPath: {_sanitize_path(result['path'])}"

    elif tool_name == "append_to_file":
        msg = f"SUCCESS: {result['message']}\nPath: {_sanitize_path(result['path'])}\nChars appended: {result['chars_added']}"
        if result.get("backup"):
            msg += f"\nBackup created."
        return msg

    else:
        return f"SUCCESS: {result.get('message', str(result))}"


# ─── LLM caller with model fallback ─────────────────────────

def _call_llm(prompt: str, auth_context) -> tuple[str, str]:
    """Try each model in sequence. Returns (response_text, model_id)."""
    for model_id in MODELS:
        try:
            chat = LLMChat(
                model_id=model_id,
                auth_context=auth_context,
                high_reasoning_effort=False,
                web_search=False,
            )
            response = chat.say(prompt)
            return response, model_id
        except Exception:
            continue
    return "ERREUR : Tous les modèles LLM ont échoué.", "none"


# ─── Regex helper ────────────────────────────────────────────

def _extract(pattern: str, text: str, dotall: bool = False) -> str | None:
    """Extract first regex match group, or None."""
    flags = re.IGNORECASE | (re.DOTALL if dotall else 0)
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


# ─── Auth init (called once by the app) ─────────────────────

def init_auth():
    """Initialize LLM authentication context."""
    return get_auth_context()
