"""
routers/transactions.py — POST /transaction/evaluate, GET /transactions, GET /transactions/export
"""
import csv
import io
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from app.database import database
from app.models import TransactionIn, TransactionOut, TransactionListOut
from app.services.policy_engine import evaluate
from app.ws_manager import manager

router = APIRouter(tags=["transactions"])


@router.post("/transaction/evaluate", response_model=TransactionOut)
async def evaluate_transaction(tx: TransactionIn):
    try:
        result = await evaluate(tx)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Broadcast transaction event to all WS clients
    await manager.broadcast({
        "type": "transaction_event",
        "data": result.model_dump(mode="json"),
    })

    # Broadcast agent spend update (so meters refresh without polling)
    spend_row = await database.fetch_one(
        "SELECT * FROM agent_spend_totals WHERE agent_id = :id",
        {"id": tx.agent_id},
    )
    if spend_row:
        from app.services.kill_switch import get_current_state
        state = await get_current_state()
        await manager.broadcast({
            "type": "agent_update",
            "data": {
                "agent_id":    spend_row["agent_id"],
                "spend_total": str(spend_row["spend_total"]),
                "spend_pct":   str(spend_row["spend_pct"]),
                "status":      "halted" if state == "killed" else "active",
            },
        })

    return result


@router.get("/transactions", response_model=TransactionListOut)
async def list_transactions(
    agent_id:    Optional[str]  = Query(None),
    decision:    Optional[str]  = Query(None),
    is_injected: Optional[bool] = Query(None),
    limit:       int            = Query(100, ge=1, le=1000),
    offset:      int            = Query(0, ge=0),
    since:       Optional[str]  = Query(None),
):
    filters = []
    params: dict = {}

    if agent_id:
        filters.append("t.agent_id = :agent_id")
        params["agent_id"] = agent_id
    if decision:
        filters.append("t.decision = :decision")
        params["decision"] = decision
    if is_injected is not None:
        filters.append("t.is_injected_misbehavior = :is_injected")
        params["is_injected"] = is_injected
    if since:
        filters.append("t.timestamp >= :since")
        params["since"] = since

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    total_row = await database.fetch_one(
        f"SELECT COUNT(*) AS cnt FROM transactions t {where}", params
    )
    total = total_row["cnt"] if total_row else 0

    rows = await database.fetch_all(
        f"""
        SELECT t.*, a.name AS agent_name
        FROM transactions t
        JOIN agents a ON a.id = t.agent_id
        {where}
        ORDER BY t.timestamp DESC
        LIMIT :limit OFFSET :offset
        """,
        {**params, "limit": limit, "offset": offset},
    )

    return TransactionListOut(
        total=total,
        limit=limit,
        offset=offset,
        transactions=[TransactionOut(**dict(r)) for r in rows],
    )


@router.get("/transactions/export")
async def export_transactions(
    agent_id:    Optional[str]  = Query(None),
    decision:    Optional[str]  = Query(None),
    is_injected: Optional[bool] = Query(None),
    since:       Optional[str]  = Query(None),
    format:      str            = Query("json", pattern="^(json|csv)$"),
):
    filters = []
    params: dict = {}

    if agent_id:
        filters.append("t.agent_id = :agent_id")
        params["agent_id"] = agent_id
    if decision:
        filters.append("t.decision = :decision")
        params["decision"] = decision
    if is_injected is not None:
        filters.append("t.is_injected_misbehavior = :is_injected")
        params["is_injected"] = is_injected
    if since:
        filters.append("t.timestamp >= :since")
        params["since"] = since

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    rows = await database.fetch_all(
        f"""
        SELECT t.*, a.name AS agent_name
        FROM transactions t
        JOIN agents a ON a.id = t.agent_id
        {where}
        ORDER BY t.timestamp ASC
        """,
        params,
    )

    records = [dict(r) for r in rows]

    if format == "csv":
        output = io.StringIO()
        if records:
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
        )

    return records
