"""One-time Garmin Connect authentication setup.

Run this script once to authenticate with Garmin Connect and store tokens.
The tokens will be saved to the directory specified by GARMIN_TOKEN_DIR
(default: ./garmin_tokens).

Usage:
    python auth_setup.py
    # or with Docker:
    docker compose run --rm garmin-mcp python auth_setup.py
"""

import os
import sys
import getpass
import logging

import garminconnect

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TOKEN_DIR = os.environ.get("GARMIN_TOKEN_DIR", "./garmin_tokens")


def main():
    print("=== Garmin Connect Authentication Setup ===\n")
    print(f"Tokens will be saved to: {TOKEN_DIR}\n")

    email = input("Garmin Connect email: ").strip()
    password = getpass.getpass("Garmin Connect password: ")

    garmin = garminconnect.Garmin(email, password)

    print("\nLogging in...")
    result = garmin.login()

    # Handle MFA if required
    if result and result[0] == "needs_mfa":
        print("\nMFA is required.")
        mfa_code = input("Enter your MFA/TOTP code: ").strip()
        garmin.resume_login(mfa_code)

    # Save tokens
    os.makedirs(TOKEN_DIR, exist_ok=True)
    garmin.client.dump(TOKEN_DIR)
    logger.info(f"Tokens saved to {TOKEN_DIR}")

    # Verify
    name = garmin.get_full_name()
    print(f"\nSuccess! Authenticated as: {name}")
    print(f"Tokens saved to: {TOKEN_DIR}")
    print("\nYou can now start the MCP server.")


if __name__ == "__main__":
    main()
