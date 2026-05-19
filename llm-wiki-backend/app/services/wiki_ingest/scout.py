"""Scout agent — exploration agentique du wiki et production du plan d'édition."""

from langsmith import traceable as _traceable

from app.config import settings
from app.services.wiki.index import build_index
from app.services.wiki_ingest.agent_loop import run_wiki_agent_loop
from app.services.wiki_ingest.edit_plan import EditPlan
from app.services.wiki_ingest.prompts import SCOUT_SYSTEM

MAX_TOOL_CALLS = 15


def traceable(func):
    if not settings.LANGSMITH_TRACING:
        return func
    return _traceable(func)


@traceable
async def run_scout(doc_text: str, project_id: str) -> EditPlan:
    wiki_index = await build_index(project_id)
    return await run_wiki_agent_loop(
        project_id=project_id,
        messages=[
            {"role": "system", "content": SCOUT_SYSTEM.format(wiki_index=wiki_index)},
            {"role": "user", "content": doc_text},
        ],
        finalize_tool_name="finalize_writing",
        max_tool_calls=MAX_TOOL_CALLS,
        label="scout",
        output_model=EditPlan,
    )
