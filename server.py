"""Garmin Connect MCP Server - HTTP transport for remote access."""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Any

import garminconnect
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GARMIN_TOKEN_DIR = os.environ.get("GARMIN_TOKEN_DIR", "/data/garmin_tokens")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))


class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Simple Bearer token authentication. Skipped if MCP_API_KEY is not set."""

    def __init__(self, app, token: str):
        super().__init__(app)
        self.token = token

    async def dispatch(self, request: Request, call_next):
        if not self.token:
            return await call_next(request)
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[7:] != self.token:
            return Response(
                '{"error":"Unauthorized"}',
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)


# --- Garmin client (lazy-initialized, module-level singleton) ---

_garmin: garminconnect.Garmin | None = None


def get_garmin() -> garminconnect.Garmin:
    global _garmin
    if _garmin is None:
        _garmin = garminconnect.Garmin()
        _garmin.login(GARMIN_TOKEN_DIR)
        logger.info("Garmin Connect authenticated from token store")
    return _garmin


# --- MCP server ---

mcp = FastMCP(
    "Garmin Connect",
    instructions=(
        "Access health and fitness data from Garmin Connect. "
        "Dates should be in YYYY-MM-DD format. "
        "When no date is specified, today's date is used."
    ),
)


def _today() -> str:
    return date.today().isoformat()


def _date_n_days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


# ---- Tools ----


@mcp.tool()
def get_daily_summary(day: str | None = None) -> dict[str, Any]:
    """Get the daily health summary for a given date.

    Includes steps, calories, heart rate, stress, body battery, floors, and intensity minutes.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_user_summary(day)


@mcp.tool()
def get_steps(start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """Get daily step counts for a date range.

    Args:
        start_date: Start date YYYY-MM-DD. Defaults to 7 days ago.
        end_date: End date YYYY-MM-DD. Defaults to today.
    """
    start_date = start_date or _date_n_days_ago(6)
    end_date = end_date or _today()
    return get_garmin().get_daily_steps(start_date, end_date)


@mcp.tool()
def get_activities(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Get recent activities (runs, rides, swims, etc.).

    Args:
        start_date: Start date YYYY-MM-DD. Defaults to 30 days ago.
        end_date: End date YYYY-MM-DD. Defaults to today.
        limit: Maximum number of activities to return (default 20, max 100).
    """
    start_date = start_date or _date_n_days_ago(29)
    end_date = end_date or _today()
    return get_garmin().get_activities_by_date(start_date, end_date, limit=limit)


@mcp.tool()
def get_activity_details(activity_id: int) -> dict[str, Any]:
    """Get detailed data for a specific activity.

    Args:
        activity_id: The numeric Garmin activity ID.
    """
    return get_garmin().get_activity_details(activity_id)


@mcp.tool()
def get_sleep_data(day: str | None = None) -> dict[str, Any]:
    """Get sleep analysis for a given date.

    Includes sleep stages (deep, light, REM, awake), duration, and score.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_sleep_data(day)


@mcp.tool()
def get_heart_rate(day: str | None = None) -> dict[str, Any]:
    """Get heart rate data for a given date.

    Includes resting heart rate and daily HR readings.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_heart_rates(day)


@mcp.tool()
def get_hrv_data(day: str | None = None) -> dict[str, Any]:
    """Get Heart Rate Variability (HRV) data for a given date.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_hrv_data(day)


@mcp.tool()
def get_stress(day: str | None = None) -> dict[str, Any]:
    """Get stress level data for a given date.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_stress_data(day)


@mcp.tool()
def get_body_battery(day: str | None = None) -> list[dict]:
    """Get body battery energy level data for a given date.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    end = day
    return get_garmin().get_body_battery(day, end)


@mcp.tool()
def get_body_composition(
    start_date: str | None = None, end_date: str | None = None
) -> dict[str, Any]:
    """Get body composition data (weight, BMI, body fat %) for a date range.

    Args:
        start_date: Start date YYYY-MM-DD. Defaults to 30 days ago.
        end_date: End date YYYY-MM-DD. Defaults to today.
    """
    start_date = start_date or _date_n_days_ago(29)
    end_date = end_date or _today()
    return get_garmin().get_body_composition(start_date, end_date)


@mcp.tool()
def get_weigh_ins(
    start_date: str | None = None, end_date: str | None = None
) -> dict[str, Any]:
    """Get weight measurements for a date range.

    Args:
        start_date: Start date YYYY-MM-DD. Defaults to 30 days ago.
        end_date: End date YYYY-MM-DD. Defaults to today.
    """
    start_date = start_date or _date_n_days_ago(29)
    end_date = end_date or _today()
    return get_garmin().get_weigh_ins(start_date, end_date)


@mcp.tool()
def get_training_readiness(day: str | None = None) -> dict[str, Any]:
    """Get training readiness score and contributing factors for a given date.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_training_readiness(day)


@mcp.tool()
def get_training_status(day: str | None = None) -> dict[str, Any]:
    """Get training status and VO2 max estimates.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_training_status(day)


@mcp.tool()
def get_spo2(day: str | None = None) -> dict[str, Any]:
    """Get blood oxygen (SpO2) data for a given date.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_spo2_data(day)


@mcp.tool()
def get_floors(day: str | None = None) -> dict[str, Any]:
    """Get floors climbed data for a given date.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_floors(day)


@mcp.tool()
def get_respiration(day: str | None = None) -> dict[str, Any]:
    """Get respiration rate data for a given date.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_respiration_data(day)


@mcp.tool()
def get_devices() -> list[dict]:
    """Get list of Garmin devices associated with the account."""
    return get_garmin().get_devices()


@mcp.tool()
def get_personal_records() -> list[dict]:
    """Get personal records (PRs) for running and other activities."""
    return get_garmin().get_personal_record()


@mcp.tool()
def get_weekly_intensity_minutes(
    start_date: str | None = None, end_date: str | None = None
) -> dict[str, Any]:
    """Get weekly intensity minutes (moderate and vigorous activity).

    Args:
        start_date: Start date YYYY-MM-DD. Defaults to 4 weeks ago.
        end_date: End date YYYY-MM-DD. Defaults to today.
    """
    start_date = start_date or _date_n_days_ago(27)
    end_date = end_date or _today()
    return get_garmin().get_weekly_intensity_minutes(start_date, end_date)


@mcp.tool()
def get_stats_and_body(day: str | None = None) -> dict[str, Any]:
    """Get combined stats and body metrics for a given date.

    Args:
        day: Date in YYYY-MM-DD format. Defaults to today.
    """
    day = day or _today()
    return get_garmin().get_stats_and_body(day)


if __name__ == "__main__":
    middleware = []
    if MCP_API_KEY:
        logger.info("MCP_API_KEY is set — Bearer token authentication enabled")
        middleware.append(
            Middleware(BearerTokenMiddleware, token=MCP_API_KEY)
        )
    else:
        logger.warning(
            "MCP_API_KEY is not set — server is open to anyone who can reach it"
        )

    mcp.run(
        transport="streamable-http",
        host=HOST,
        port=PORT,
        middleware=middleware,
        allowed_origins=["*"],
    )
