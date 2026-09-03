"""
00_check_oci_auth.py
====================
Pre-flight diagnostic for OCI auth.

Before blaming MCP for a 401, run this. It uses the OCI Python SDK
directly - no MCP, no subprocess - to call the same Usage API the
MCP server wraps.

OUTCOMES
--------
- If this script SUCCEEDS:
    OCI auth is fine. Any 401 from 01_oci_usage_mcp_client.py is an
    MCP-environment issue (likely the {**os.environ, ...} merge).

- If this script FAILS with 401:
    The problem is in your OCI auth config, NOT MCP. The MCP layer is
    just faithfully forwarding a request that OCI itself rejects. Fix
    the auth here first, then 01_oci_usage_mcp_client.py will work.

AUTH TYPE
---------
This script auto-detects which auth method your ~/.oci/config uses:

  * API key  - recommended for this course. Set up once with
               `oci setup config`. Doesn't expire on a timer; rotate
               manually when you choose to. Best for demos, CI, and
               anywhere you don't want auth refreshes interrupting flow.

  * Session token - what you get from `oci session authenticate`.
               Expires every ~60 minutes by default. Refresh with
               `oci session refresh --profile-name DEFAULT`. Useful
               for human SSO flows; painful for course recordings.

Either works for this lesson. The {**os.environ, ...} subprocess fix
applies to both: with session tokens, the SDK needs USERPROFILE/HOME
to expand `~` in security_token_file; with API keys, it needs the
same env vars to expand `~` in key_file.

PREREQUISITES
-------------
    pip install oci

This is the official OCI Python SDK. It's a transitive dependency of
oci-cli, so if you've already done `pip install oci-cli` you have it.
"""

import configparser
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import oci


PROFILE = "DEFAULT"
CONFIG_PATH = Path.home() / ".oci" / "config"


def show_config_summary() -> dict:
    """Load the OCI config and print exactly what we resolved."""
    print("=" * 60)
    print("Config inspection")
    print("=" * 60)
    print(f"Config file : {CONFIG_PATH}")
    print(f"Profile     : {PROFILE}")
    print()

    if not CONFIG_PATH.exists():
        print(f"ERROR: config file not found at {CONFIG_PATH}")
        sys.exit(1)

    # Use OCI's loader, not just configparser, so path expansion matches
    # what the SDK actually sees at request time.
    config = oci.config.from_file(str(CONFIG_PATH), PROFILE)

    print(f"Region      : {config.get('region')}")
    tenancy = config.get("tenancy", "")
    print(f"Tenancy     : {tenancy[:25]}...{tenancy[-10:]}")

    using_session = bool(config.get("security_token_file"))
    if using_session:
        token_path = Path(config["security_token_file"]).expanduser()
        print(f"Auth type   : session token")
        print(f"Token file  : {token_path}")
        print(f"Token exists: {token_path.exists()}")
        if token_path.exists():
            mtime = datetime.fromtimestamp(token_path.stat().st_mtime, tz=timezone.utc)
            age = datetime.now(timezone.utc) - mtime
            print(f"Token age   : {int(age.total_seconds() / 60)} minutes "
                  f"(default lifetime is ~60 minutes)")
    else:
        print(f"Auth type   : API key")
        print(f"User OCID   : {config.get('user', '')[:25]}...")
        print(f"Fingerprint : {config.get('fingerprint')}")
        key_path = Path(config["key_file"]).expanduser()
        print(f"Key file    : {key_path}")
        print(f"Key exists  : {key_path.exists()}")
    print()
    return config


def build_signer(config: dict):
    """Build the right kind of signer for whichever auth type the
    config uses. The OCI SDK can usually figure this out from the
    config alone, but doing it explicitly here makes the diagnostic
    output clearer."""
    if config.get("security_token_file"):
        token_path = Path(config["security_token_file"]).expanduser()
        token = token_path.read_text().strip()
        private_key = oci.signer.load_private_key_from_file(config["key_file"])
        return oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config["key_file"],
    )


def test_identity(config, signer) -> bool:
    """Smoke test: list_regions. Lightweight, no special policies needed.
    If THIS fails, your auth is fundamentally broken."""
    print("=" * 60)
    print("Test 1: Identity API (list_regions)")
    print("=" * 60)
    try:
        identity = oci.identity.IdentityClient(config, signer=signer)
        regions = identity.list_regions().data
        print(f"PASSED - {len(regions)} regions returned\n")
        return True
    except Exception as exc:
        print(f"FAILED: {exc}\n")
        return False


def test_usage_api(config, signer) -> bool:
    """Real test: the same call the MCP server makes."""
    print("=" * 60)
    print("Test 2: Usage API (request_summarized_usages)")
    print("=" * 60)
    try:
        usage = oci.usage_api.UsageapiClient(config, signer=signer)
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        details = oci.usage_api.models.RequestSummarizedUsagesDetails(
            tenant_id=config["tenancy"],
            time_usage_started=today - timedelta(days=7),
            time_usage_ended=today,
            granularity="DAILY",
            query_type="COST",
            group_by=["service"],
            compartment_depth=1,
        )
        result = usage.request_summarized_usages(details).data
        n = len(result.items) if result.items else 0
        print(f"PASSED - {n} usage records returned\n")
        return True
    except Exception as exc:
        print(f"FAILED: {exc}\n")
        return False


def main() -> None:
    config = show_config_summary()
    signer = build_signer(config)

    identity_ok = test_identity(config, signer)
    usage_ok = test_usage_api(config, signer) if identity_ok else False

    print("=" * 60)
    print("Diagnosis")
    print("=" * 60)

    if identity_ok and usage_ok:
        print(
            "OCI auth is working end-to-end.\n"
            "If 01_oci_usage_mcp_client.py still fails with 401, the\n"
            "issue is the MCP subprocess environment. Verify that your\n"
            "StdioServerParameters has env={**os.environ, ...} (NOT just\n"
            "env={...} - the latter wipes USERPROFILE/HOME from the\n"
            "subprocess and the OCI SDK can't expand `~` in your config)."
        )
    elif identity_ok and not usage_ok:
        print(
            "Identity works but Usage API doesn't. This is an authorization\n"
            "issue (your IAM policies), not authentication. Add or verify:\n"
            "    Allow group <your-group> to read usage-report in tenancy\n"
            "Note: even though the error says 401, OCI's Usage API sometimes\n"
            "returns 401 for missing usage-report read access (it should be\n"
            "403, but it isn't always)."
        )
    else:
        print(
            "Authentication itself is broken. MCP is not the problem.\n\n"
            "If you're using session tokens (auth type above):\n"
            "    oci session validate\n"
            "    oci session refresh --profile-name DEFAULT\n"
            "    # if refresh window closed, re-authenticate:\n"
            f"    oci session authenticate --profile-name DEFAULT --region {config.get('region')}\n\n"
            "If you're using API keys (auth type above):\n"
            "    1. Verify fingerprint in ~/.oci/config matches OCI Console\n"
            "       (Profile -> API Keys for your user).\n"
            "    2. Verify key_file path is correct and the file is readable.\n"
            "    3. Verify the public key in OCI Console matches your private key."
        )


if __name__ == "__main__":
    main()
