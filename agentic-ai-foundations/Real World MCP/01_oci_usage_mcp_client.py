"""
01_oci_usage_mcp_client.py
==========================
Real-world MCP demo: calling Oracle's published OCI Usage MCP server.

In your earlier MCP lessons, you wrote BOTH the server (mcp_math_server.py)
and the client (02_first_agent_with_mcp.py). That was great for learning
the mechanics, but in the real world you almost never write the server -
you connect to one that someone else (a vendor, a SaaS, an internal team)
has already published.

This file shows that pattern. We don't write a server. We just connect to
Oracle's OCI Usage MCP server, ask it what tools it has, and then call one.

ARCHITECTURE
------------
    +------------------+   stdio    +-------------------------+   HTTPS
    | this Python file | <--------> | oracle.oci-usage-mcp-   | <------>  OCI Usage API
    | (the MCP client) |            | server (Oracle's code)  |
    +------------------+            +-------------------------+

We never call the OCI Usage REST API directly. The MCP server does that
for us, using the OCI CLI profile in %USERPROFILE%\\.oci\\config.

OUTPUT
------
We call get_summarized_usage for the last 7 days, grouped by SERVICE at
DAILY granularity, and produce TWO views of the result:

    1. A pivoted table printed to the terminal, for a quick glance.
    2. A CSV file (oci_daily_cost.csv) you can open in Excel / Sheets.

Open OCI Console -> Billing & Cost Management -> Cost Analysis with the
same filters (Daily / Cost / Group by: Service / same dates), open the
CSV in Excel beside it, and the numbers should line up to the cent.

THREE REAL-WORLD MCP LESSONS BAKED INTO THIS FILE
-------------------------------------------------
1. DOCS LIE. SCHEMAS DON'T. Always print the runtime schema with
   list_tools() before coding the call - the server is its own source
   of truth. Oracle's docs page lists tools that don't exist in the
   shipped package.

2. SUBPROCESSES DON'T INHERIT YOUR SHELL ENV BY DEFAULT. Use
   env={**os.environ, ...}, otherwise the OCI SDK can't expand `~` in
   key_file paths and you get a 401 even though your config works
   everywhere else.

3. CHOOSE THE RIGHT AUTH FOR THE JOB. This course uses OCI API keys
   (set up once with `oci setup config`). They don't expire on a
   timer, so demos and recordings aren't interrupted by `oci session
   refresh` every 60 minutes. Session tokens are still useful for SSO
   workflows, but for learning and CI, API keys are the right call.

PREREQUISITES (run once)
------------------------
1. pip install mcp
2. uv installed (Windows): powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
3. pip install oci-cli && oci setup config
   - "oci setup config" generates an RSA keypair, uploads the public
     half to your OCI user, and writes ~/.oci/config with key_file,
     fingerprint, user, tenancy, and region populated.
4. Tenancy admin policy: Allow group <grp> to read usage-report in tenancy
"""

import asyncio
import configparser
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ----------------------------------------------------------------------
# Read tenancy OCID from ~/.oci/config (no hardcoding).
# ----------------------------------------------------------------------
def get_tenancy_ocid(profile: str = "DEFAULT") -> str:
    parser = configparser.ConfigParser()
    parser.read(Path.home() / ".oci" / "config")
    return parser[profile]["tenancy"]


# ----------------------------------------------------------------------
# Server launch parameters.
# Note the {**os.environ, ...} - without it the spawned subprocess won't
# inherit USERPROFILE/HOME, and the OCI SDK inside the server will fail
# to expand `~` in your config's key_file/security_token_file paths.
#
# OCI_CLI_AUTH=api_key tells the OCI MCP server to use the API-key code
# path. Without this, oracle.oci-usage-mcp-server's get_summarized_usage
# handler does a hardcoded dict lookup for `security_token_file` and
# crashes with KeyError on API-key configs. Setting this env var routes
# it through the API-key signer instead. Valid values:
#   api_key, security_token, instance_principal, resource_principal,
#   instance_obo_user, oke_workload_identity
# ----------------------------------------------------------------------
server_params = StdioServerParameters(
    command="uvx",
    args=["oracle.oci-usage-mcp-server"],
    env={
        **os.environ,
        "OCI_CONFIG_PROFILE": "DEFAULT",
        "OCI_CLI_AUTH": "api_key",
        "FASTMCP_LOG_LEVEL": "ERROR",
    },
)


# ----------------------------------------------------------------------
# Response unwrapping. OCI MCP responses can be wrapped a few different
# ways depending on server version; this collapses them to a flat list.
# ----------------------------------------------------------------------
def extract_items(parsed) -> list:
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("items", "data"):
            if key in parsed:
                return extract_items(parsed[key])
    return []


# ----------------------------------------------------------------------
# Pivot helper: turn a flat list of {date, service, amount} records
# into a date-by-service grid plus row/column totals. Both the table
# printer and the CSV writer use the same pivot, so terminal and CSV
# always agree.
# ----------------------------------------------------------------------
def build_pivot(items: list) -> dict | None:
    if not items:
        return None

    grid: dict = defaultdict(lambda: defaultdict(float))
    services: set = set()
    currency = "USD"

    for item in items:
        ts = item.get("time_usage_started") or ""
        date_str = ts[:10] if ts else "?"
        service = item.get("service") or "(unspecified)"
        amount = float(item.get("computed_amount") or 0.0)
        currency = item.get("currency") or currency
        grid[date_str][service] += amount
        services.add(service)

    dates = sorted(grid.keys())
    services_sorted = sorted(services)
    column_totals = {
        s: sum(grid[d].get(s, 0.0) for d in dates) for s in services_sorted
    }
    grand_total = sum(column_totals.values())

    return {
        "dates": dates,
        "services": services_sorted,
        "grid": grid,
        "column_totals": column_totals,
        "grand_total": grand_total,
        "currency": currency,
    }


def print_daily_service_table(pivot: dict | None) -> None:
    """Print the pivot to the terminal, padded for readability."""
    if pivot is None:
        print("(no usage records returned for this window)")
        return

    dates = pivot["dates"]
    services = pivot["services"]
    grid = pivot["grid"]
    column_totals = pivot["column_totals"]
    grand_total = pivot["grand_total"]
    currency = pivot["currency"]

    date_w = max(len("Date (UTC)"), max(len(d) for d in dates))
    svc_w = {s: max(len(s), 10) for s in services}
    total_label = f"Total ({currency})"
    total_w = max(len(total_label), 10)
    sep = "  "

    header = f"{'Date (UTC)':<{date_w}}"
    for s in services:
        header += sep + f"{s:>{svc_w[s]}}"
    header += sep + f"{total_label:>{total_w}}"
    print(header)
    print("-" * len(header))

    for d in dates:
        row = f"{d:<{date_w}}"
        day_total = 0.0
        for s in services:
            v = grid[d].get(s, 0.0)
            row += sep + f"{v:>{svc_w[s]}.2f}"
            day_total += v
        row += sep + f"{day_total:>{total_w}.2f}"
        print(row)

    print("-" * len(header))
    total_row = f"{total_label:<{date_w}}"
    for s in services:
        total_row += sep + f"{column_totals[s]:>{svc_w[s]}.2f}"
    total_row += sep + f"{grand_total:>{total_w}.2f}"
    print(total_row)


def write_daily_service_csv(pivot: dict | None, filepath: Path) -> None:
    """Write the same pivot to a CSV file. Open it in Excel / Google
    Sheets / Numbers to compare against the OCI console row-by-row."""
    if pivot is None:
        return

    services = pivot["services"]
    grid = pivot["grid"]
    column_totals = pivot["column_totals"]
    grand_total = pivot["grand_total"]
    currency = pivot["currency"]
    total_label = f"Total ({currency})"

    with filepath.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(["Date (UTC)"] + services + [total_label])

        # Data rows
        for d in pivot["dates"]:
            row = [d]
            day_total = 0.0
            for s in services:
                v = grid[d].get(s, 0.0)
                row.append(round(v, 2))   # 2 decimals to match console display
                day_total += v
            row.append(round(day_total, 2))
            writer.writerow(row)

        # Total row
        total_row = [total_label]
        for s in services:
            total_row.append(round(column_totals[s], 2))
        total_row.append(round(grand_total, 2))
        writer.writerow(total_row)


def render_tool_result(result, csv_path: Path) -> None:
    """Parse the MCP tool result, print the table, and write the CSV."""
    raw_text = ""
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            raw_text += text

    try:
        parsed = json.loads(raw_text)
    except (ValueError, TypeError):
        print(raw_text)
        return

    items = extract_items(parsed)
    pivot = build_pivot(items)
    print_daily_service_table(pivot)
    write_daily_service_csv(pivot, csv_path)
    print()
    if pivot is not None:
        print(f"Wrote CSV: {csv_path.resolve()}")
        print("Open it in Excel / Google Sheets to compare against the OCI Console.")


async def main() -> None:
    print("Launching the OCI Usage MCP server via `uvx`...\n")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:

            await session.initialize()
            print("MCP session initialized.\n")

            # Schema discovery - the server is its own source of truth.
            tools_response = await session.list_tools()
            print("Tools exposed by oracle.oci-usage-mcp-server")
            print("=" * 60)
            for tool in tools_response.tools:
                print(f"\nTool: {tool.name}")
                if tool.description:
                    for line in tool.description.strip().splitlines()[:3]:
                        print(f"  {line}")
                print("  Input schema (properties):")
                props = (tool.inputSchema or {}).get("properties", {})
                required = set((tool.inputSchema or {}).get("required", []))
                for prop_name, prop_def in props.items():
                    flag = " (required)" if prop_name in required else ""
                    prop_type = prop_def.get("type", "?")
                    print(f"    - {prop_name}: {prop_type}{flag}")
            print()

            # Build arguments. These mirror the OCI Console's Cost
            # Analysis filters: last 7 days, Daily, Cost, Group by Service.
            tenancy_ocid = get_tenancy_ocid("DEFAULT")
            today_utc = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start = today_utc - timedelta(days=30)
            end = today_utc

            arguments = {
                "tenant_id": tenancy_ocid,
                "start_time": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_time": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "group_by": ["service"],
                "compartment_depth": 1,
                "granularity": "DAILY",
                "query_type": "COST",
            }

            print("Calling tool: get_summarized_usage")
            print("=" * 60)
            print("Arguments:")
            print(json.dumps(arguments, indent=2))
            print()

            try:
                result = await session.call_tool(
                    "get_summarized_usage",
                    arguments=arguments,
                )
                print(
                    f"Daily cost by service "
                    f"(start {arguments['start_time']}, "
                    f"end {arguments['end_time']})"
                )
                print("=" * 60)

                # Write the CSV next to this script for predictable location.
                csv_path = Path(__file__).resolve().parent / "oci_daily_cost.csv"
                render_tool_result(result, csv_path)

            except Exception as exc:
                print(f"Tool call failed: {exc}\n")
                print(
                    "Common causes:\n"
                    "  1. Subprocess didn't inherit USERPROFILE/HOME -\n"
                    "     the {**os.environ, ...} above is what fixes that.\n"
                    "  2. Missing IAM policy:\n"
                    "       Allow group <grp> to read usage-report in tenancy\n"
                    "  3. Try query_type='USAGE' if 'COST' returns nothing.\n"
                    "  4. API key issues:\n"
                    "       - private key file at config's key_file path missing/unreadable\n"
                    "       - public key removed/rotated in OCI Console\n"
                    "       - fingerprint in config doesn't match the uploaded public key\n"
                    "  5. Run 00_check_oci_auth.py to isolate auth issues.\n"
                )


if __name__ == "__main__":
    asyncio.run(main())
