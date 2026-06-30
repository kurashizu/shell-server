from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.jail import SecurityError
from app.schemas import ExecRequest, ExecResponse, ExecStreamRequest

router = APIRouter()


@router.post(
    "/exec",
    response_model=ExecResponse,
    summary="Execute a command",
    description="Run a command in the sandboxed workspace and return its output, "
    "stderr, exit code, and execution time.",
)
async def exec_command(req: ExecRequest, request: Request):
    executor = request.app.state.executor
    workspace = request.app.state.workspace

    try:
        result = await executor.execute(
            command=req.command,
            args=req.args,
            timeout_secs=req.timeout_secs,
            env=req.env or None,
            cwd=workspace.root,
            shell=req.shell,
        )
    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return result


@router.post(
    "/exec/stream",
    summary="Execute a command (SSE stream)",
    description="Run a command and stream stdout/stderr in real time via "
    "Server-Sent Events. The last event contains the exit code.",
)
async def exec_stream(req: ExecStreamRequest, request: Request):
    executor = request.app.state.executor
    workspace = request.app.state.workspace

    async def event_generator():
        try:
            async for event in executor.stream_execute(
                command=req.command,
                args=req.args,
                timeout_secs=req.timeout_secs,
                env=req.env or None,
                cwd=workspace.root,
                shell=req.shell,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except SecurityError as e:
            yield f"data: {json.dumps({'stream': 'error', 'text': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
