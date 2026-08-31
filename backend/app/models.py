"""
models.py — Pydantic request/response schemas.
All DB row shapes, API payloads, and WebSocket event envelopes.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class Decision(str, Enum):
    allowed = "allowed"
    denied  = "denied"
    flagged = "flagged"


class KillSwitchState(str, Enum):
    active = "active"
    killed = "killed"


class MisbehaviorType(str, Enum):
    overspend = "overspend"
    off_scope = "off_scope"
    burst     = "burst"
    random    = "random"  # only valid in inject request; resolved before logging


class LLMSource(str, Enum):
    sim          = "sim"
    llm_hosted   = "llm-hosted"
    llm_local    = "llm-local"


class AgentStatus(str, Enum):
    active = "active"
    halted = "halted"


# ── Agent schemas ─────────────────────────────────────────────────────────────

class AgentOut(BaseModel):
    id:          str
    name:        str
    category:    str
    spend_cap:   Decimal
    rate_limit:  Optional[int]
    spend_total: Decimal
    spend_pct:   Decimal
    status:      AgentStatus

    class Config:
        from_attributes = True


class AgentDetailOut(AgentOut):
    recent_transactions: list[TransactionOut] = []


# ── Transaction schemas ───────────────────────────────────────────────────────

class TransactionIn(BaseModel):
    agent_id:               str
    amount:                 Decimal = Field(gt=0)
    category:               str
    is_injected_misbehavior: bool    = False
    misbehavior_type:       Optional[MisbehaviorType] = None
    source:                 LLMSource = LLMSource.sim


class TransactionOut(BaseModel):
    id:                     str
    agent_id:               str
    agent_name:             Optional[str] = None   # joined in list queries
    amount:                 Decimal
    category:               str
    timestamp:              datetime
    decision:               Decision
    reason:                 Optional[str]
    is_injected_misbehavior: bool
    misbehavior_type:       Optional[str]
    source:                 LLMSource = LLMSource.sim
    # Graceful degradation (fallback fields) deferred — see CONTEXT.md.
    # fallback_status:        Optional[str] = None
    # fallback_reason:        Optional[str] = None
    # resolved_at:            Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionListOut(BaseModel):
    total:        int
    limit:        int
    offset:       int
    transactions: list[TransactionOut]


# ── Kill switch schemas ───────────────────────────────────────────────────────

class KillSwitchOut(BaseModel):
    state:        KillSwitchState
    last_changed: datetime
    triggered_by: str


class KillSwitchIn(BaseModel):
    triggered_by: str = "manual"


class KillSwitchHistoryItem(BaseModel):
    id:           int
    state:        KillSwitchState
    timestamp:    datetime
    triggered_by: str


# ── Simulator schemas ─────────────────────────────────────────────────────────

class LastInjection(BaseModel):
    agent_id:        str
    misbehavior_type: str
    timestamp:       datetime


class SimulatorStatusOut(BaseModel):
    running:              bool
    normal_interval_ms:   int
    injection_probability: float
    last_injection:       Optional[LastInjection] = None


class SimulatorStartIn(BaseModel):
    normal_interval_ms:    int   = 1500
    injection_probability: float = Field(0.15, ge=0.0, le=1.0)


class InjectIn(BaseModel):
    agent_id:        Optional[str]          = None   # None = random
    misbehavior_type: MisbehaviorType       = MisbehaviorType.random


# ── WebSocket event envelopes ─────────────────────────────────────────────────

class WSTransactionEvent(BaseModel):
    type: str = "transaction_event"
    data: TransactionOut


class WSKillSwitchEvent(BaseModel):
    type: str = "kill_switch_event"
    data: KillSwitchOut


class WSAgentUpdate(BaseModel):
    type:        str = "agent_update"
    data: AgentOut


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorOut(BaseModel):
    detail: str
    code:   str


# ── Auth schemas ────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id:          str
    email:       str
    full_name:   Optional[str]
    is_active:   bool
    created_at:  datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email:       str
    password:    str
    full_name:   Optional[str] = None


class UserLogin(BaseModel):
    email:       str
    password:    str


class Token(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class TokenPayload(BaseModel):
    sub:   str
    exp:   int
    type:  str  # "access" or "refresh"


class TokenRefresh(BaseModel):
    refresh_token: str


# resolve forward refs
AgentDetailOut.model_rebuild()
