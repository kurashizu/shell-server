# Shell Server — API Reference for Agents

Base URL: `http://{host}:{port}` (default `http://127.0.0.1:8080`)

## Authentication (optional)

If `SHELL_SERVER_AUTH_TOKEN` is set on the server, all API requests
(except `/docs`, `/redoc`, `/openapi.json`) require:

```
Authorization: Bearer <token>
```

Missing token → `401`, wrong token → `403`.

## Endpoints

### POST /api/exec

Execute a command. Waits for completion, returns full result.

Request:
```json
{
  "command": "ls",
  "args": ["-la"],
  "shell": false,
  "timeout_secs": 30,
  "env": {}
}
```

- `shell: true` — runs via `bash -c` so pipes (`|`), redirects (`>`)
  and shell syntax work. `command` + `args` are joined with spaces.
- `timeout_secs` — capped at server max (default 300). Server default
  is usually 30.
- `env` — extra environment variables merged into the process.

Response `200`:
```json
{
  "stdout": "...",
  "stderr": "...",
  "exit_code": 0,
  "duration_ms": 12.34,
  "truncated": false,
  "error": null
}
```

- `exit_code: -1` means timeout or command not found.
- `truncated: true` means output exceeded the server limit (1 MB by
  default); the tail is replaced with `\n... [truncated]`.
- `error` is set when timeout or command-not-found occurs.

### POST /api/exec/stream

Same as `/api/exec` but returns output as Server-Sent Events (SSE).

Each event is `data: <json>\n\n`:

```
data: {"stream": "stdout", "text": "line1\n"}
data: {"stream": "stderr", "text": "error line\n"}
data: {"stream": "exit", "exit_code": 0, "duration_ms": 5.2, "error": null}
```

The final event has `"stream": "exit"`. `error` is set on timeout.

### GET /api/workspace/files

List files in the workspace.

Query: `?subpath=dir1` (optional, default is workspace root)

Response:
```json
{
  "files": [
    {"name": "foo.txt", "path": "foo.txt", "type": "file", "size": 123},
    {"name": "mydir", "path": "mydir", "type": "dir", "size": 0}
  ]
}
```

### GET /api/workspace/files/{path}

Read a file. Returns raw bytes (`application/octet-stream`).

### POST /api/workspace/files/{path}

Write a file. Body is raw bytes; parent directories created automatically.

### DELETE /api/workspace/files/{path}

Delete a file or directory. Cannot delete workspace root.

### POST /api/workspace/reset

Delete all contents of the workspace and recreate it empty.

## Important behaviors

1. **Workspace jail** — all commands run with `cwd` forced to the
   workspace directory. Path traversal in file operations is blocked.
2. **Command whitelist** — if configured on the server, only listed
   commands are allowed. `shell: true` validates the first token.
3. **Timeout** — commands are killed after the timeout. Default 30s,
   max 300s.
4. **Output limit** — stdout/stderr are each truncated at 1 MB by
   default.
5. **File paths** are relative to workspace root. Use `/` as separator.
