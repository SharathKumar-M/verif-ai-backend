from typing import TypedDict, List, Optional, Annotated, Literal, Dict
import operator
from pydantic import BaseModel, Field
from datetime import datetime

class AgentFlag(BaseModel):
    type: str
    detail: str
    severity: Literal["high", "medium", "low"]

class ResearchStep(BaseModel):
    step: int
    agent: str
    thought: str
    action: str
    query: str
    sources: List[str]
    finding: str
    impact: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_ms: int

class ResumeAgentResult(BaseModel):
    ai_text_probability: float
    skill_inflation_score: float
    timeline_consistency_score: float
    overall_resume_trust: float
    skills_claimed: List[str] = Field(default_factory=list)
    experience_start_dates: Dict[str, str] = Field(default_factory=dict, description="Company name to ISO start date")
    flags: List[AgentFlag]
    research_steps: List[ResearchStep]
    summary: str

class CertAgentResult(BaseModel):
    forgery_probability: float
    issuer_verified: bool
    visual_tampering_score: float
    overall_cert_trust: float
    course_names: List[str] = Field(default_factory=list)
    flags: List[AgentFlag]
    research_steps: List[ResearchStep]
    summary: str

class GitHubAgentResult(BaseModel):
    originality_score: float
    skill_match_score: float
    commit_authenticity_score: float
    overall_github_trust: float
    languages_used: List[str] = Field(default_factory=list)
    earliest_commit_by_language: Dict[str, str] = Field(default_factory=dict, description="Language to ISO date")
    flags: List[AgentFlag]
    research_steps: List[ResearchStep]
    summary: str

class VerificationState(TypedDict):
    student_uid: str
    resume_doc_id: str
    cert_doc_ids: List[str]
    github_url: str
    resume_result: Optional[dict]
    cert_result: Optional[dict]
    github_result: Optional[dict]
    cross_ref_findings: Optional[List[str]]
    research_logs: Annotated[List[dict], operator.add]   # append-only
    flags: Annotated[List[dict], operator.add]           # append-only
    completed_agents: Annotated[List[str], operator.add] # append-only
    overall_trust_score: Optional[float]
    verdict: Optional[str]
