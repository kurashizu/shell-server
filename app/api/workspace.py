from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.core.jail import SecurityError
from app.schemas import WorkspaceListResponse, WorkspaceResetResponse

router = APIRouter()


@router.get(
    "/workspace/files",
    response_model=WorkspaceListResponse,
    summary="List workspace files",
    description="List all files and directories in the workspace (or a subpath).",
)
async def list_files(subpath: str = "", request: Request = None):
    workspace = request.app.state.workspace
    try:
        files = workspace.list_files(subpath)
    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {"files": files}


@router.get(
    "/workspace/files/{path:path}",
    summary="Read a workspace file",
    description="Read the raw content of a file in the workspace.",
)
async def read_file(path: str, request: Request):
    workspace = request.app.state.workspace
    try:
        content = workspace.read_file(path)
    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return Response(content=content, media_type="application/octet-stream")


@router.post(
    "/workspace/files/{path:path}",
    summary="Write a workspace file",
    description="Write raw content (binary) to a file in the workspace. "
    "Parent directories are created automatically.",
)
async def write_file(path: str, request: Request):
    workspace = request.app.state.workspace
    body = await request.body()
    try:
        workspace.write_file(path, body)
    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {"message": f"Written {len(body)} bytes to {path}"}


@router.delete(
    "/workspace/files/{path:path}",
    summary="Delete a workspace file",
    description="Delete a file or directory from the workspace.",
)
async def delete_file(path: str, request: Request):
    workspace = request.app.state.workspace
    try:
        workspace.delete_path(path)
    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {"message": f"Deleted: {path}"}


@router.post(
    "/workspace/reset",
    response_model=WorkspaceResetResponse,
    summary="Reset workspace",
    description="Delete all contents of the workspace and recreate it empty.",
)
async def reset_workspace(request: Request):
    workspace = request.app.state.workspace
    workspace.reset()
    return {"message": "Workspace has been reset"}
