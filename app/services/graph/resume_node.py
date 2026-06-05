import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any

from app.services.graph.state import VerificationState, ResumeAgentResult, ResearchStep, AgentFlag
from app.services.tools.pdf_tools import extract_pdf_text
from app.services.tools.stylometry_tools import analyze_text_locally, extract_skills
from app.services.tools.web_tools import web_search_tool
from app.core.langchain_setup import get_gemini_flash
from app.core.firebase import get_firestore

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)

async def resume_agent_node(state: VerificationState) -> dict:
    """
    Analyzes the resume for fraud signals using Gemini 1.5 Flash and web search.
    """
    try:
        student_uid = state.get("student_uid")
        resume_doc_id = state.get("resume_doc_id")
        
        if not resume_doc_id:
            return {"error": "No resume document ID provided in state"}

        # 1 & 2. Extract Text
        resume_text = await extract_pdf_text.ainvoke({"gridfs_doc_id": resume_doc_id, "bucket_name": "resumes"})
        if resume_text.startswith("Error"):
            raise Exception(resume_text)

        # 3 & 4. Stylometry and Skills
        stylometry = analyze_text_locally(resume_text)
        skills_list = extract_skills(resume_text)

        # 5. Build System Prompt
        with open("contracts/resume-agent.md", "r") as f:
            system_prompt_template = f.read()

        # Load structured output model
        llm = get_gemini_flash(streaming=True)
        structured_llm = llm.with_structured_output(ResumeAgentResult, method="json_schema")

        # 6. Create LangGraph Agent
        # Note: We use a separate agent for tool usage, then aggregate into structured output
        tools = [web_search_tool]
        agent_executor = create_react_agent(llm, tools)

        # Define the investigation task
        investigation_query = f"""
        INVESTIGATE THIS RESUME:
        ---
        {resume_text[:3000]}
        ---
        STYLOMETRY SIGNALS:
        {json.dumps(stylometry, indent=2)}
        
        CLAIMED SKILLS (AUTOMATICALLY EXTRACTED):
        {", ".join(skills_list)}
        
        GOAL: Verify companies, check skill inflation, and calculate trust scores.
        """

        research_steps = []
        
        # 7. Run via astream_events to capture research steps
        # We wrap the react agent logic
        inputs = {"messages": [SystemMessage(content=system_prompt_template), HumanMessage(content=investigation_query)]}
        
        async for event in agent_executor.astream_events(inputs, version="v2"):
            kind = event["event"]
            if kind == "on_tool_start":
                research_steps.append({
                    "step": len(research_steps) + 1,
                    "agent": "resume",
                    "thought": "Using web search to verify claims...",
                    "action": "web_search",
                    "query": event["data"].get("input", {}).get("query", ""),
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif kind == "on_tool_end":
                if research_steps:
                    research_steps[-1]["finding"] = str(event["data"].get("output", ""))
                    research_steps[-1]["duration_ms"] = 0 # Placeholder

        # 8. Get Structured Result
        # Final pass to summarize everything into the structured schema
        final_prompt = f"""
        Based on your research and the following resume details, provide the final structured assessment.
        
        RESUME:
        {resume_text[:2000]}
        
        RESEARCH LOGS:
        {json.dumps(research_steps, indent=2)}
        
        STRICTLY return JSON matching ResumeAgentResult.
        """
        
        result: ResumeAgentResult = await structured_llm.ainvoke(final_prompt)
        
        # Hydrate research steps in the result object
        # Converting raw dicts to ResearchStep models
        final_research_steps = []
        for i, rs in enumerate(research_steps):
            final_research_steps.append(ResearchStep(
                step=rs["step"],
                agent="resume",
                thought=rs["thought"],
                action=rs["action"],
                query=rs["query"],
                sources=[], # Would need parsing from finding if needed
                finding=rs.get("finding", ""),
                impact="NEUTRAL", # Default
                duration_ms=0
            ))
        result.research_steps = final_research_steps

        # 9 & 10. Save to Firestore
        db = get_firestore()
        result_id = str(uuid.uuid4())
        
        # Save AI Result
        ai_result_data = result.model_dump()
        ai_result_data["student_uid"] = student_uid
        ai_result_data["agent_type"] = "resume"
        ai_result_data["created_at"] = datetime.utcnow()
        await db.collection("ai_results").document(result_id).set(ai_result_data)
        
        # Save Research Logs
        logs_data = {
            "result_id": result_id,
            "student_uid": student_uid,
            "agent_type": "resume",
            "logs": [rs.model_dump() for rs in final_research_steps],
            "created_at": datetime.utcnow()
        }
        await db.collection("research_logs").document(result_id).set(logs_data)

        return {
            "resume_result": result.model_dump(),
            "research_logs": [rs.model_dump() for rs in final_research_steps],
            "completed_agents": ["resume"],
            "flags": [f.model_dump() for f in result.flags]
        }

    except Exception as e:
        logger.error(f"Resume agent node failure: {str(e)}")
        # 11. Fallback
        fallback_result = ResumeAgentResult(
            ai_text_probability=0.5,
            skill_inflation_score=50.0,
            timeline_consistency_score=50.0,
            overall_resume_trust=50.0,
            flags=[AgentFlag(type="SYSTEM_ERROR", detail=str(e), severity="high")],
            research_steps=[],
            summary=f"Analysis failed: {str(e)}"
        )
        return {
            "resume_result": fallback_result.model_dump(),
            "research_logs": [],
            "completed_agents": ["resume"],
            "flags": [f.model_dump() for f in fallback_result.flags]
        }
