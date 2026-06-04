import json
import logging
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any

from app.services.graph.state import VerificationState, GitHubAgentResult, ResearchStep, AgentFlag
from app.services.tools.github_tools import (
    get_github_profile, 
    analyze_github_repos, 
    analyze_commit_patterns
)
from app.services.tools.web_tools import web_search_tool
from app.core.langchain_setup import get_gemini_flash
from app.core.firebase import get_firestore

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)

async def github_agent_node(state: VerificationState) -> dict:
    """Analyzes student's GitHub profile and cross-references with resume data."""
    try:
        github_url = state.get("github_url")
        student_uid = state.get("student_uid")
        
        if not github_url:
            return {
                "github_result": GitHubAgentResult(
                    originality_score=0.0,
                    skill_match_score=0.0,
                    commit_authenticity_score=0.0,
                    overall_github_trust=0.0,
                    flags=[AgentFlag(type="MISSING_GITHUB", detail="No GitHub URL provided", severity="high")],
                    research_steps=[],
                    summary="GitHub analysis skipped: No URL provided."
                ).model_dump(),
                "completed_agents": ["github"]
            }

        # 1. Gather raw signals in parallel
        profile_task = get_github_profile.ainvoke({"github_url": github_url})
        repos_task = analyze_github_repos.ainvoke({"github_url": github_url})
        commits_task = analyze_commit_patterns.ainvoke({"github_url": github_url})
        
        profile, repos, commits = await asyncio.gather(profile_task, repos_task, commits_task)

        # 2. Get resume skills for cross-reference
        resume_result = state.get("resume_result") or {}
        # Assuming resume_result has a 'summary' or we can extract skills from its text if available
        # But usually, it should have some processed data. Let's look for 'skills' or similar.
        # In a real flow, the resume_node would have populated this.
        resume_summary = resume_result.get("summary", "No resume summary available.")
        
        with open("contracts/github-agent.md", "r") as f:
            system_prompt = f.read()

        llm = get_gemini_flash(streaming=True)
        tools = [web_search_tool] # Agent can use web search to verify developer identity/company
        
        agent_executor = create_react_agent(llm, tools)
        
        research_steps = []
        
        investigation_query = f"""
        INVESTIGATE THIS GITHUB PROFILE: {github_url}
        
        RAW SIGNALS:
        - Profile: {json.dumps(profile, indent=2)}
        - Repos: {json.dumps(repos, indent=2)}
        - Commit Patterns: {json.dumps(commits, indent=2)}
        
        CROSS-REFERENCE WITH RESUME DATA:
        {resume_summary}
        
        Identify any red flags (fake commits, suspicious fork ratio, skill mismatch).
        Verify identity if possible.
        """
        
        inputs = {"messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=investigation_query)
        ]}
        
        async for event in agent_executor.astream_events(inputs, version="v2"):
            kind = event["event"]
            if kind == "on_tool_start":
                research_steps.append({
                    "step": len(research_steps) + 1,
                    "agent": "github",
                    "thought": "Running OSINT investigation...",
                    "action": event["name"],
                    "query": event["data"].get("input", {}).get("query", ""),
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif kind == "on_tool_end":
                if research_steps:
                    research_steps[-1]["finding"] = str(event["data"].get("output", ""))
                    research_steps[-1]["duration_ms"] = 0

        # 3. Get Structured Output
        structured_llm = llm.with_structured_output(GitHubAgentResult, method="json_schema")
        
        final_prompt = f"""
        Based on the raw signals and your investigation steps, provide the final structured assessment.
        
        RESEARCH STEPS TAKEN:
        {json.dumps(research_steps, indent=2)}
        
        RAW DATA:
        {json.dumps({"profile": profile, "repos": repos, "commits": commits}, indent=2)}
        
        STRICTLY return JSON matching GitHubAgentResult.
        """
        
        result: GitHubAgentResult = await structured_llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=final_prompt)
        ])
        
        # 4. Hydrate research steps
        result.research_steps = [
            ResearchStep(
                step=rs["step"], 
                agent="github", 
                thought=rs["thought"], 
                action=rs["action"], 
                query=rs["query"], 
                sources=[], 
                finding=rs.get("finding", ""), 
                impact="NEUTRAL", 
                duration_ms=0
            ) for rs in research_steps
        ]

        # 5. Save to Firestore
        db = get_firestore()
        result_id = str(uuid.uuid4())
        
        ai_result_data = result.model_dump()
        ai_result_data["student_uid"] = student_uid
        ai_result_data["agent_type"] = "github"
        ai_result_data["created_at"] = datetime.utcnow()
        await db.collection("ai_results").document(result_id).set(ai_result_data)
        
        logs_data = {
            "result_id": result_id,
            "student_uid": student_uid,
            "agent_type": "github",
            "logs": [rs.model_dump() for rs in result.research_steps],
            "created_at": datetime.utcnow()
        }
        await db.collection("research_logs").document(result_id).set(logs_data)

        return {
            "github_result": result.model_dump(),
            "research_logs": [rs.model_dump() for rs in result.research_steps],
            "completed_agents": ["github"],
            "flags": [f.model_dump() for f in result.flags]
        }

    except Exception as e:
        logger.error(f"GitHub agent node failure: {str(e)}")
        fallback = GitHubAgentResult(
            originality_score=50.0,
            skill_match_score=50.0,
            commit_authenticity_score=50.0,
            overall_github_trust=50.0,
            flags=[AgentFlag(type="SYSTEM_ERROR", detail=str(e), severity="high")],
            research_steps=[],
            summary=f"Analysis failed: {str(e)}"
        )
        return {
            "github_result": fallback.model_dump(),
            "research_logs": [],
            "completed_agents": ["github"],
            "flags": [f.model_dump() for f in fallback.flags]
        }
