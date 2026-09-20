# Garmin Connect MCP Server

An HTTP MCP server that exposes your Garmin Connect health and fitness data to Claude (and any MCP-compatible AI client). Designed for remote access from phones, tablets, and other computers.

## Stack

- **[fastmcp](https://github.com/jlowin/fastmcp)** — MCP server framework with HTTP transport
- **[garminconnect](https://github.com/cyberjunky/python-garminconnect)** — Garmin Connect API client
- **Docker** — easy deployment anywhere

## Setup

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set a strong `MCP_API_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Authenticate with Garmin Connect

This one-time step logs in with your Garmin credentials and saves OAuth tokens to a Docker volume.

```bash
docker compose run --rm garmin-mcp python auth_setup.py
```

You'll be prompted for your email, password, and MFA code (if enabled). Tokens are stored in the `garmin_tokens` Docker volume and automatically refreshed.

### 3. Start the server

```bash
docker compose up -d
```

The MCP endpoint is now available at:
```
http://your-server-ip:8000/mcp
```

### 4. Connect Claude

#### Claude.ai (web / mobile)

Go to **Settings → Integrations → Add MCP server** and enter:

- **URL**: `http://your-server-ip:8000/mcp`
- **Authorization**: `Bearer your-api-key`

#### Claude Code (CLI)

Add to your `~/.claude/claude.json` or project `.claude/claude.json`:

```json
{
  "mcpServers": {
    "garmin": {
      "type": "http",
      "url": "http://your-server-ip:8000/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

#### Other MCP clients (SSE transport)

If your client requires SSE instead of streamable-HTTP, set `TRANSPORT=sse` in `.env` and point to `http://your-server-ip:8000/sse`.

---

## Available Tools

| Tool | Description |
|------|-------------|
| `get_daily_summary` | Steps, calories, HR, stress, body battery, floors |
| `get_steps` | Daily step counts for a date range |
| `get_activities` | List recent activities (runs, rides, swims…) |
| `get_activity_details` | Full data for a specific activity |
| `get_sleep_data` | Sleep stages, duration, and score |
| `get_heart_rate` | Resting and daily heart rate readings |
| `get_hrv_data` | Heart Rate Variability (HRV) |
| `get_stress` | Stress level throughout the day |
| `get_body_battery` | Energy level (body battery) |
| `get_body_composition` | Weight, BMI, body fat % |
| `get_weigh_ins` | Weight measurements |
| `get_training_readiness` | Training readiness score |
| `get_training_status` | Training status and VO2 max |
| `get_spo2` | Blood oxygen (SpO2) |
| `get_floors` | Floors climbed |
| `get_respiration` | Respiration rate |
| `get_devices` | Connected Garmin devices |
| `get_personal_records` | Personal records (PRs) |
| `get_weekly_intensity_minutes` | Weekly moderate/vigorous activity |
| `get_stats_and_body` | Combined daily stats + body metrics |

---

## Running without Docker

```bash
pip install -r requirements.txt

# One-time auth
GARMIN_TOKEN_DIR=./garmin_tokens python auth_setup.py

# Start server
GARMIN_TOKEN_DIR=./garmin_tokens MCP_API_KEY=your-key python server.py
```

## Security Notes

- Always set `MCP_API_KEY` — without it the server is open to anyone who can reach it.
- Put the server behind a reverse proxy (nginx/Caddy) with HTTPS for production use.
- Garmin tokens are stored in a Docker volume and refreshed automatically.
