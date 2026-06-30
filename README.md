# Shell Server

A RESTful API for executing shell commands in a sandboxed workspace.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run (development, auto-reload)
make dev

# Or run (production)
make run
```

Open **http://127.0.0.1:8080/docs** for the interactive Swagger UI (auto-generated).

> If authentication is enabled (`SHELL_SERVER_AUTH_TOKEN` is set), click the
> **Authorize** button on the Swagger page and enter your token once; all
> subsequent "Try it out" requests will include it automatically.

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/exec` | Execute a command, return full result |
| `POST` | `/api/exec/stream` | Execute a command, stream output via SSE |
| `GET` | `/api/workspace/files` | List workspace files |
| `GET` | `/api/workspace/files/{path}` | Read a file |
| `POST` | `/api/workspace/files/{path}` | Write a file |
| `DELETE` | `/api/workspace/files/{path}` | Delete a file |
| `POST` | `/api/workspace/reset` | Clear the workspace |

## Examples

> If authentication is enabled, add `-H "Authorization: Bearer <token>"`
> to every curl command below.

```bash
# Execute a command
curl -s http://127.0.0.1:8080/api/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "echo", "args": ["hello world"]}' | jq .

# Write then read a file
curl -s -X POST http://127.0.0.1:8080/api/workspace/files/hello.txt \
  -d "Hello from shell-server"

curl -s http://127.0.0.1:8080/api/workspace/files/hello.txt

# Stream a long-running command
curl -s -N http://127.0.0.1:8080/api/exec/stream \
  -H "Content-Type: application/json" \
  -d '{"command": "ping", "args": ["-c", "3", "127.0.0.1"]}'
```

## Configuration

Set via environment variables with the `SHELL_SERVER_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `SHELL_SERVER_HOST` | `127.0.0.1` | Bind address |
| `SHELL_SERVER_PORT` | `8080` | Port |
| `SHELL_SERVER_WORKSPACE_PATH` | `/tmp/shell-server-workspace` | Workspace directory |
| `SHELL_SERVER_DEFAULT_TIMEOUT` | `30` | Default command timeout (s) |
| `SHELL_SERVER_MAX_TIMEOUT` | `300` | Max allowed timeout (s) |
| `SHELL_SERVER_MAX_OUTPUT_SIZE` | `1048576` | Max output size per stream (bytes) |
| `SHELL_SERVER_ALLOWED_COMMANDS` | `""` | Comma-separated whitelist (empty = allow all) |
| `SHELL_SERVER_AUTH_TOKEN` | `""` | Bearer token for auth (empty = no auth). See [Authentication](#authentication) below. |

## Security

- **Workspace jail**: all commands run with `cwd` set to the workspace directory
- **Path traversal prevention**: workspace file operations validate that resolved paths stay within the workspace
- **No shell injection**: uses `asyncio.create_subprocess_exec()` with explicit args, not a shell string
- **Timeouts & output limits**: commands are killed after timeout; output is truncated at the configured limit
- **Command whitelist**: optional; when set, only listed commands are allowed

## Authentication

Set `SHELL_SERVER_AUTH_TOKEN` to enable Bearer token authentication:

```bash
SHELL_SERVER_AUTH_TOKEN=my-secret-token make dev
```

Requests without a token are rejected with **401**, and requests with an
incorrect token are rejected with **403**:

```bash
# ❌ 401 — no token
curl -s http://127.0.0.1:8080/api/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "echo", "args": ["hi"]}'
# {"detail":"Missing or malformed Authorization header..."}

# ❌ 403 — wrong token
curl -s http://127.0.0.1:8080/api/exec \
  -H "Authorization: Bearer wrong-token" \
  -H "Content-Type: application/json" \
  -d '{"command": "echo", "args": ["hi"]}'
# {"detail":"Invalid token"}

# ✅ 200 — correct token
curl -s http://127.0.0.1:8080/api/exec \
  -H "Authorization: Bearer my-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"command": "echo", "args": ["hi"]}'
# {"stdout": "hi\n", "exit_code": 0, ...}
```

The documentation pages (`/docs`, `/redoc`, `/openapi.json`) are always
accessible without authentication, and Swagger UI has an **Authorize**
button so you can enter the token once and try endpoints interactively.
