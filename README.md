# Shell Server

A RESTful API for executing shell commands in a sandboxed workspace,
with command whitelisting, timeout control, output truncation, and
optional Bearer token authentication.

## Quick Start

```bash
git clone https://github.com/kurashizu/shell-server.git
cd shell-server

make install           # create .venv + install dependencies
make dev               # start with auto-reload (development)

# or for production:
# make run
```

Open **http://127.0.0.1:8080/docs** for the interactive Swagger UI
— all API endpoints, request/response schemas, and authentication are
documented there.

## Deployment

```bash
# 1. Clone and install
git clone https://github.com/kurashizu/shell-server.git
cd shell-server
make install

# 2. Configure (optional)
cp .env.example .env
# edit .env as needed

# 3. Start (production)
make run
```

### Configuration

All settings are controlled via environment variables with the
`SHELL_SERVER_` prefix, or by editing `.env`:

| Variable | Default | Description |
|---|---|---|
| `SHELL_SERVER_HOST` | `127.0.0.1` | Bind address |
| `SHELL_SERVER_PORT` | `8080` | Port |
| `SHELL_SERVER_WORKSPACE_PATH` | `/tmp/shell-server-workspace` | Workspace directory |
| `SHELL_SERVER_DEFAULT_TIMEOUT` | `30` | Default command timeout (s) |
| `SHELL_SERVER_MAX_TIMEOUT` | `300` | Maximum allowed timeout (s) |
| `SHELL_SERVER_MAX_OUTPUT_SIZE` | `1048576` | Max bytes per stdout/stderr stream |
| `SHELL_SERVER_ALLOWED_COMMANDS` | `""` | Comma-separated or JSON command whitelist |
| `SHELL_SERVER_AUTH_TOKEN` | `""` | Bearer token (empty = no auth) |
| `SHELL_SERVER_DOMAIN` | `""` | Public domain for OpenAPI `servers` field |

Example:

```bash
SHELL_SERVER_PORT=9090 SHELL_SERVER_ALLOWED_COMMANDS=echo,ls,git make run
```

### Run with Docker (example)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "run.py"]
```

```bash
docker build -t shell-server .
docker run -p 8080:8080 -e SHELL_SERVER_AUTH_TOKEN=secret shell-server
```

## Security

- **Workspace jail** — commands run in an isolated directory; path
  traversal is blocked
- **Shell injection prevention** — uses `exec()` with explicit args,
  not a shell string (unless `shell: true` is requested)
- **Timeouts & output limits** — commands are killed after timeout;
  output is truncated at the configured limit
- **Command whitelist** — optional, restricts which executables are allowed
- **Auth** — optional Bearer token; documented in Swagger UI

## API Documentation

All API details — endpoints, request/response schemas, authentication,
and interactive testing — are available at:

- **Swagger UI** — `/docs`
- **ReDoc** — `/redoc`
- **OpenAPI JSON** — `/openapi.json`
