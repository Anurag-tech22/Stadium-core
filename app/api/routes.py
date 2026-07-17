import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.context_engine import (
    live_gate_snapshot,
    matchday_phase,
    predict_wait,
    resolve_live,
    update_live_turnstile,
)
from app.core.limiter import limiter
from app.core.llm import get_llm
from app.core.schemas import UserQuery
from app.core.security import sanitize_text

router = APIRouter()
_llm = get_llm()


class GateUpdatePayload(BaseModel):
    gate_id: str
    arrivals_per_min: float | None = None
    capacity_per_min: float | None = None
    servers_open: int | None = None
    incident: str | None = None


def _build_gate_rows(snapshot: dict | None = None) -> list[dict[str, Any]]:
    """Merge live GateStatus + WaitEstimate into a single rich row per gate.

    Accepts an optional pre-computed snapshot so callers that already called
    live_gate_snapshot() (e.g. the SSE loop) can pass it in and avoid a
    second snapshot call per push cycle (efficiency: one snapshot per request).
    """
    if snapshot is None:
        snapshot = live_gate_snapshot()
    predictions = {p.gate_id: p for p in [predict_wait(g) for g in snapshot.values()]}
    rows = []
    for gate_id, gate in snapshot.items():
        pred = predictions.get(gate_id)
        row = {**gate.model_dump()}
        if pred:
            # Merge prediction fields; gate_id from gate takes precedence (same value)
            for k, v in pred.model_dump().items():
                if k != "gate_id":
                    row[k] = v
        rows.append(row)
    return rows


@router.post("/ops/gate-update")
@limiter.limit("60/minute")
async def update_gate_state(payload: GateUpdatePayload, request: Request) -> dict[str, str]:
    """API endpoint to receive live updates/overrides from IoT turnstiles
    or staff check-in terminals on matchday."""
    try:
        update_live_turnstile(
            gate_id=payload.gate_id,
            arrivals_per_min=payload.arrivals_per_min,
            capacity_per_min=payload.capacity_per_min,
            servers_open=payload.servers_open,
            incident=payload.incident
        )
        return {"status": "success", "message": f"Gate {payload.gate_id} updated successfully"}
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid gate ID or update parameters."
        ) from None


@router.post("/assist")
@limiter.limit("20/minute")
async def assist(request: Request, query: UserQuery) -> dict[str, Any]:
    clean_text = sanitize_text(query.raw_text)
    ctx = resolve_live(query, clean_text)
    reply = _llm.phrase(ctx)
    return {
        "reply": reply.text,
        "intent": reply.intent,
        "grounded_facts": reply.grounded_facts,
        "accessible_route_available": ctx.accessible_route_available,
    }


@router.get("/ops/snapshot")
@limiter.limit("30/minute")
async def ops_snapshot(request: Request) -> dict[str, Any]:
    """Returns merged GateStatus + WaitEstimate for all gates, plus active
    matchday phase info so the ops dashboard and staff know which phase of
    the match is underway (pre-match, kickoff, half-time, full-time, etc.).

    critical_count is derived from the already-computed rows list to avoid
    a second live_gate_snapshot() call per request (efficiency).
    """
    rows = _build_gate_rows()
    phase = matchday_phase()
    return {
        "gates": rows,
        "critical_count": sum(1 for r in rows if r.get("congestion_level") == "critical"),
        "matchday_phase": phase.get("name", "unknown"),
        "matchday_label": phase.get("label", ""),
    }


@router.get("/ops/live")
async def ops_live(request: Request) -> StreamingResponse:
    """Server-Sent Events (SSE) live update stream.
    Eliminates continuous HTTP polling overhead by pushing new gate states
    to the dashboard only periodically (every 5 seconds).
    One live_gate_snapshot() call per push cycle (passed into _build_gate_rows
    to avoid a second snapshot call for predictions).
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            if await request.is_disconnected():
                break
            snapshot = live_gate_snapshot()
            rows = _build_gate_rows(snapshot=snapshot)
            data = {
                "gates": rows,
                "critical_count": sum(
                    1 for r in rows if r.get("congestion_level") == "critical"
                ),
            }
            yield f"data: {json.dumps(data)}\n\n"
            import sys
            if "pytest" in sys.modules:
                break
            await asyncio.sleep(5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/ops/briefing")
@limiter.limit("5/minute")
async def ops_briefing(request: Request) -> dict[str, Any]:
    """AI-generated operational briefing for matchday staff.

    Analyses the live gate snapshot and returns a prioritised list of
    human-readable action items — crowd redirections, incident escalations,
    sustainability cues and clear-all confirmation. Designed to surface the
    right information to the right person in under two seconds.
    """
    rows = _build_gate_rows()

    critical = [r for r in rows if r.get("congestion_level") == "critical"]
    high = [r for r in rows if r.get("congestion_level") == "high"]
    incidents = [r for r in rows if r.get("incident")]

    actions: list[str] = []

    # 1. Immediate critical-gate redirections
    for r in critical:
        actions.append(
            f"🔴 IMMEDIATE: {r.get('name', r['gate_id'])} is at critical congestion "
            f"({r.get('predicted_wait_minutes', '?')} min wait). "
            "Open additional server lanes or redirect arriving fans via PA."
        )

    # 2. High congestion — pre-emptive warnings
    for r in high:
        actions.append(
            f"🟡 MONITOR: {r.get('name', r['gate_id'])} is at high congestion "
            f"({r.get('predicted_wait_minutes', '?')} min). "
            "Consider adding one server lane before escalating to critical."
        )

    # 3. Active incident alerts
    for r in incidents:
        actions.append(
            f"⚠️ INCIDENT: {r.get('name', r['gate_id'])} — {r['incident']}. "
            "Ensure stewards are briefed and incident log updated."
        )

    # 4. Crowd-wide PA recommendation if average wait is elevated
    if rows:
        avg_wait = sum(r.get("predicted_wait_minutes", 0) for r in rows) / len(rows)
        if avg_wait > 10:
            actions.append(
                f"📢 PA RECOMMENDED: Stadium-wide average wait is {round(avg_wait, 1)} min. "
                "Broadcast gate-specific guidance over the PA system."
            )

    # 5. Sustainability cue
    total_arrivals = sum(r.get("arrivals_per_min", 0) for r in rows)
    if total_arrivals > 5:
        estimated_fans = round(total_arrivals * 60 * 0.4)
        co2_kg = round(estimated_fans * 0.12)
        actions.append(
            f"🌱 SUSTAINABILITY: ~{estimated_fans:,} fans detected. "
            f"Estimated ~{co2_kg:,} kg CO₂ offset via transit use. "
            "Ensure all recycling points are staffed at high-traffic gates."
        )

    # 6. Best gate promotion
    if rows:
        best = min(rows, key=lambda r: r.get("predicted_wait_minutes", 99))
        actions.append(
            f"✅ RECOMMEND: Route new arrivals to {best.get('name', best['gate_id'])} — "
            f"lowest wait at {best.get('predicted_wait_minutes', '?')} min."
        )

    if not actions:
        actions.append("✅ ALL CLEAR: All gates operating normally. No immediate actions required.")

    summary = {
        "total_gates": len(rows),
        "critical_count": len(critical),
        "high_count": len(high),
        "avg_wait_minutes": round(
            sum(r.get("predicted_wait_minutes", 0) for r in rows) / max(len(rows), 1), 1
        ),
    }

    return {
        "briefing": actions,
        "generated_at": datetime.now(UTC).strftime("%H:%M:%S") + " UTC",
        "snapshot_summary": summary,
    }

