import json
import logging
import uuid
import base64
from datetime import datetime
from typing import List, Dict, Any
from bson import ObjectId
from io import BytesIO

from app.services.graph.state import VerificationState, CertAgentResult, ResearchStep, AgentFlag
from app.services.tools.pdf_tools import extract_pdf_text, extract_pdf_metadata
from app.services.tools.image_tools import error_level_analysis, ocr_extract_text
from app.services.tools.web_tools import web_search_tool
from app.core.langchain_setup import get_gemini_vision
from app.core.firebase import get_firestore
from app.core.database import get_gridfs

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)

async def analyze_single_certificate(doc_id: str, student_uid: str) -> CertAgentResult:
    """Analyzes a single certificate (PDF or Image) and returns CertAgentResult."""
    try:
        bucket = get_gridfs("certificates")
        grid_out = await bucket.open_download_stream(ObjectId(doc_id))
        file_bytes = await grid_out.read()
        
        # 2. Detect mime
        header = file_bytes[:512]
        is_pdf = header.startswith(b'%PDF')
        is_jpeg = header.startswith(b'\xff\xd8')
        is_png = header.startswith(b'\x89PNG')
        
        with open("contracts/certificate-agent.md", "r") as f:
            system_prompt = f.read()

        llm_vision = get_gemini_vision(streaming=True)
        structured_llm = llm_vision.with_structured_output(CertAgentResult, method="json_schema")
        
        research_steps = []
        
        if is_pdf:
            # 3. PDF Logic
            metadata = await extract_pdf_metadata.invoke(doc_id)
            text = await extract_pdf_text.invoke(doc_id)
            
            prompt = f"""
            ANALYZE THIS PDF CERTIFICATE:
            
            METADATA:
            {json.dumps(metadata, indent=2)}
            
            EXTRACTED TEXT:
            {text}
            
            INVESTIGATE and return final CertAgentResult.
            """
            # For PDF we still use the structured output directly as we have text + metadata
            result: CertAgentResult = await structured_llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ])
            return result

        elif is_jpeg or is_png:
            # 4. Image Logic
            ela_score = error_level_analysis(file_bytes)
            ocr_text = await ocr_extract_text.invoke(doc_id)
            
            # Base64 encode for vision
            img_b64 = base64.b64encode(file_bytes).decode('utf-8')
            mime_type = "image/jpeg" if is_jpeg else "image/png"
            
            # For images, we use a react agent to allow web search for organization verification
            tools = [web_search_tool]
            agent_executor = create_react_agent(llm_vision, tools)
            
            image_message = {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{img_b64}"}
            }
            
            investigation_query = f"""
            ANALYZE THIS CERTIFICATE IMAGE:
            
            ELA SCORE: {ela_score:.2f} (Suspicious if > 15.0)
            OCR TEXT:
            {ocr_text}
            
            Verify the issuer and course existence via web search.
            """
            
            inputs = {"messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=[
                    {"type": "text", "text": investigation_query},
                    image_message
                ])
            ]}
            
            async for event in agent_executor.astream_events(inputs, version="v2"):
                kind = event["event"]
                if kind == "on_tool_start":
                    research_steps.append({
                        "step": len(research_steps) + 1,
                        "agent": "certificate",
                        "thought": "Verifying issuer on web...",
                        "action": "web_search",
                        "query": event["data"].get("input", {}).get("query", ""),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                elif kind == "on_tool_end":
                    if research_steps:
                        research_steps[-1]["finding"] = str(event["data"].get("output", ""))
                        research_steps[-1]["duration_ms"] = 0

            # Final summary into structured output
            final_prompt = f"""
            Based on your forensics analysis, ELA score ({ela_score:.2f}), and research logs, provide the final structured assessment.
            
            RESEARCH LOGS:
            {json.dumps(research_steps, indent=2)}
            
            STRICTLY return JSON matching CertAgentResult.
            """
            
            # For multimodal summary, we pass the image again to be sure
            result: CertAgentResult = await structured_llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=[
                    {"type": "text", "text": final_prompt},
                    image_message
                ])
            ])
            
            # Hydrate steps
            result.research_steps = [
                ResearchStep(
                    step=rs["step"], 
                    agent="certificate", 
                    thought=rs["thought"], 
                    action=rs["action"], 
                    query=rs["query"], 
                    sources=[], 
                    finding=rs.get("finding", ""), 
                    impact="NEUTRAL", 
                    duration_ms=0
                ) for rs in research_steps
            ]
            return result
        else:
            raise Exception("Unsupported file format for certificate")

    except Exception as e:
        logger.error(f"Single cert analysis error ({doc_id}): {str(e)}")
        return CertAgentResult(
            forgery_probability=0.5,
            issuer_verified=False,
            visual_tampering_score=50.0,
            overall_cert_trust=50.0,
            flags=[AgentFlag(type="CERT_ERROR", detail=f"Doc {doc_id}: {str(e)}", severity="medium")],
            research_steps=[],
            summary=f"Analysis failed for doc {doc_id}"
        )

async def certificate_agent_node(state: VerificationState) -> dict:
    """Aggregates analysis for multiple certificates."""
    try:
        cert_doc_ids = state.get("cert_doc_ids", [])
        student_uid = state.get("student_uid")
        
        if not cert_doc_ids:
            return {"error": "No certificate document IDs provided"}

        results: List[CertAgentResult] = []
        for doc_id in cert_doc_ids:
            res = await analyze_single_certificate(doc_id, student_uid)
            results.append(res)

        # Aggregate scores
        avg_forgery = sum(r.forgery_probability for r in results) / len(results)
        all_issuer_verified = all(r.issuer_verified for r in results)
        avg_tampering = sum(r.visual_tampering_score for r in results) / len(results)
        avg_trust = sum(r.overall_cert_trust for r in results) / len(results)
        
        # Merge flags and research logs
        merged_flags = []
        all_logs = []
        for r in results:
            merged_flags.extend(r.flags)
            all_logs.extend(r.research_steps)

        aggregated = CertAgentResult(
            forgery_probability=avg_forgery,
            issuer_verified=all_issuer_verified,
            visual_tampering_score=avg_tampering,
            overall_cert_trust=avg_trust,
            flags=merged_flags,
            research_steps=all_logs,
            summary=f"Analyzed {len(results)} certificates. Mixed findings." if len(results) > 1 else results[0].summary
        )

        # Save to Firestore
        db = get_firestore()
        result_id = str(uuid.uuid4())
        
        ai_result_data = aggregated.model_dump()
        ai_result_data["student_uid"] = student_uid
        ai_result_data["agent_type"] = "certificate"
        ai_result_data["created_at"] = datetime.utcnow()
        await db.collection("ai_results").document(result_id).set(ai_result_data)
        
        logs_data = {
            "result_id": result_id,
            "student_uid": student_uid,
            "agent_type": "certificate",
            "logs": [rs.model_dump() for rs in all_logs],
            "created_at": datetime.utcnow()
        }
        await db.collection("research_logs").document(result_id).set(logs_data)

        return {
            "cert_result": aggregated.model_dump(),
            "research_logs": [rs.model_dump() for rs in all_logs],
            "completed_agents": ["certificate"],
            "flags": [f.model_dump() for f in merged_flags]
        }

    except Exception as e:
        logger.error(f"Certificate agent node failure: {str(e)}")
        fallback = CertAgentResult(
            forgery_probability=0.5,
            issuer_verified=False,
            visual_tampering_score=50.0,
            overall_cert_trust=50.0,
            flags=[AgentFlag(type="SYSTEM_ERROR", detail=str(e), severity="high")],
            research_steps=[],
            summary=f"Analysis failed: {str(e)}"
        )
        return {
            "cert_result": fallback.model_dump(),
            "research_logs": [],
            "completed_agents": ["certificate"],
            "flags": [f.model_dump() for f in fallback.flags]
        }
