"""Pydantic response schemas for agent outputs.

Lightweight models to validate and coerce LLM JSON responses from agents.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, conint


class CollectorResponse(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    b2b_b2c: Optional[str] = None
    price: Optional[float] = None
    revenue: Optional[float] = None
    traffic: Optional[str] = None
    description: Optional[str] = None
    problem_solved: Optional[str] = None
    target_users: Optional[str] = None
    monetization_model: Optional[str] = None


class AnalyzerResponse(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    ai_opportunities: List[str] = Field(default_factory=list)
    competition_level: Optional[str] = None
    missing_info: List[str] = Field(default_factory=list)
    analysis_summary: Optional[str] = None


class GrowthResponse(BaseModel):
    growth_levers: List[str] = Field(default_factory=list)
    quick_wins: List[str] = Field(default_factory=list)
    growth_confidence: Optional[str] = None
    growth_rationale: Optional[str] = None


class ScoringResponse(BaseModel):
    market_potential: conint(ge=0, le=25) = 0
    ai_leverage: conint(ge=0, le=25) = 0
    ease_of_improvement: conint(ge=0, le=20) = 0
    revenue_stability: conint(ge=0, le=20) = 0
    entry_cost_fit: conint(ge=0, le=10) = 0
    confidence: conint(ge=0, le=100) = 0
    reasoning: Optional[str] = None


class DueDiligenceResponse(BaseModel):
    missing_info: List[str] = Field(default_factory=list)
    due_diligence_risks: List[str] = Field(default_factory=list)
    questions_for_seller: List[str] = Field(default_factory=list)
    dd_summary: Optional[str] = None
