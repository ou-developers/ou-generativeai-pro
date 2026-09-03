"""
02_oci_usage_mcp_agent.py
=========================
Real-world MCP demo: calling Oracle's published OCI Usage MCP server.

In your earlier MCP lessons, you wrote BOTH the server (mcp_math_server.py)
and the client (first_agent_with_mcp.py). That was great for learning
the mechanics, but in the real world you almost never write the server -
you connect to one that someone else (a vendor, a SaaS, an internal team)
has already published.

This file shows that pattern. We don't write a server. We just connect to
Oracle's OCI Usage MCP server, ask it what tools it has, and then call one.

User can ask natural-language questions and let the LLM decide when to call
which tool.

This is the same pattern your earlier course used with the math server
(MultiServerMCPClient + create_agent). The only thing that changes here
is the *server*: instead of your local Python math server, we point the
client at Oracle's published OCI Usage MCP server.

ARCHITECTURE
------------
    user (natural language)
        |
        v
    +---------+   +---------------------+   stdio    +--------------------+
    |   LLM   |<->| LangChain Agent     |<---------->| oracle.oci-usage-  |
    | (chat)  |   | (create_agent)      |            | mcp-server         |
    +---------+   +---------------------+            +--------------------+
        |                    |                                |  HTTPS
        |                    v                                v
        |          ToolMessage (raw JSON)              OCI Usage API
        |                    |
        v                    v
    final reply       deterministic table + CSV
        |                    |
        +--------------------+
                  v
            output to user

OUTPUT
------
We call get_summarized_usage for the last 30 days, grouped by SERVICE at
DAILY granularity, and produce TWO views of the result:

    1. A pivoted table printed to the terminal, for a quick glance.
    2. A CSV file (oci_daily_cost_agent.csv) you can open in Excel / Sheets.

Open OCI Console -> Billing & Cost Management -> Cost Analysis with the
same filters (Daily / Cost / Group by: Service / same dates), open the
CSV in Excel beside it, and the numbers should line up to the cent.

PREREQUISITES
-------------
    pip install mcp langchain langchain-openai langchain-mcp-adapters langgraph
    set OPENAI_API_KEY=<your-key>

OCI auth: this course uses API keys, not session tokens. If you haven't
already set up OCI, run:

    pip install oci-cli
    oci setup config

That generates a keypair, uploads the public key to your OCI user, and
writes ~/.oci/config. API keys don't expire on a timer, so you won't
have to refresh credentials mid-demo. (If you DO use session tokens,
run `oci session refresh --profile-name DEFAULT` before running this
script if it's been more than an hour since you authenticated.)
"""

import asyncio
import configparser
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
import os
from pathlib import Path
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

script_dir = Path(__file__).resolve().parent
env_path = script_dir / ".env"

#print("Current working directory:", os.getcwd())
#print("Script directory:", script_dir)
#print("Using .env from:", env_path)

load_dotenv(dotenv_path=env_path)

print("OPENAI_API_KEY found:", bool(os.getenv("OPENAI_API_KEY")))

# ----------------------------------------------------------------------
# OCI config helper.
# ----------------------------------------------------------------------
def get_tenancy_ocid(profile: str = "DEFAULT") -> str:
    parser = configparser.ConfigParser()
    parser.read(Path.home() / ".oci" / "config")
    return parser[profile]["tenancy"]


# ----------------------------------------------------------------------
# Deterministic table-rendering helpers (same logic as file 01).
# Duplicated here so each lesson file is self-contained.
# ----------------------------------------------------------------------
def extract_items(parsed) -> list:
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("items", "data"):
            if key in parsed:
                return extract_items(parsed[key])
    return []


def build_pivot(items: list) -> dict | None:
    """Pivot OCI usage records into a date-by-service grid plus totals.
    Both the printer and the CSV writer consume this same structure, so
    terminal and file output are guaranteed to agree."""
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
    """Write the same pivot to CSV. Open in Excel for column-aligned
    side-by-side comparison with the OCI Console."""
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

        writer.writerow(["Date (UTC)"] + services + [total_label])

        for d in pivot["dates"]:
            row = [d]
            day_total = 0.0
            for s in services:
                v = grid[d].get(s, 0.0)
                row.append(round(v, 2))
                day_total += v
            row.append(round(day_total, 2))
            writer.writerow(row)

        total_row = [total_label]
        for s in services:
            total_row.append(round(column_totals[s], 2))
        total_row.append(round(grand_total, 2))
        writer.writerow(total_row)


def find_last_tool_result(messages, tool_name: str) -> str | None:
    """Walk message history backwards for the most recent ToolMessage
    produced by `tool_name`. Returns its content as a string."""
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == tool_name:
            content = msg.content
            if isinstance(content, list):
                # Newer LangChain versions can return content as a list
                # of content blocks instead of a single string.
                content = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            return content
    return None


async def main() -> None:
    tenancy_ocid = get_tenancy_ocid("DEFAULT")
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ------------------------------------------------------------------
    # Register the MCP server.
    # NOTE the {**os.environ, ...} - without it the spawned uvx
    # subprocess loses USERPROFILE/HOME and OCI auth fails with 401.
    # NOTE OCI_CLI_AUTH=api_key - tells the server to use the API-key
    # code path. Without it, oracle.oci-usage-mcp-server crashes with
    # KeyError: 'security_token_file' on API-key configs.
    # ------------------------------------------------------------------
    mcp_client = MultiServerMCPClient(
        {
            "oci_usage": {
                "command": "uvx",
                "args": ["oracle.oci-usage-mcp-server"],
                "transport": "stdio",
                "env": {
                    **os.environ,
                    "OCI_CONFIG_PROFILE": "DEFAULT",
                    "OCI_CLI_AUTH": "api_key",
                    "FASTMCP_LOG_LEVEL": "ERROR",
                },
            },
        }
    )

    tools = await mcp_client.get_tools()
    print(f"Loaded {len(tools)} tool(s) from the OCI Usage MCP server:")
    for tool in tools:
        first_line = tool.description.splitlines()[0] if tool.description else ""
        print(f"  - {tool.name}: {first_line}")
    print()

    # ------------------------------------------------------------------
    # Build the agent. parallel_tool_calls=False keeps the agent loop
    # deterministic. The system prompt teaches the LLM the argument
    # contract and explicitly forbids it from rendering tables itself.
    # ------------------------------------------------------------------
    llm = ChatOpenAI(model="gpt-5.5", parallel_tool_calls=False)

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=(
            "You are an Oracle Cloud Infrastructure (OCI) cost-and-usage "
            "assistant.\n\n"
            f"The user's tenancy OCID is: {tenancy_ocid}\n"
            f"Today's date in UTC is: {today_utc}\n\n"
            "Use the get_summarized_usage tool to answer questions. "
            "Required arguments:\n"
            "  - tenant_id: the tenancy OCID above\n"
            "  - start_time: ISO 8601, MUST be midnight UTC "
            "(e.g. 2024-01-01T00:00:00Z)\n"
            "  - end_time: ISO 8601, midnight UTC, exclusive\n"
            "  - group_by: array of dimensions. Use [\"service\"] for "
            "service breakdowns, [\"compartmentName\"] for per-compartment, "
            "[\"skuName\"] for sku-level, or [] for a single total.\n"
            "  - compartment_depth: integer, use 1 unless the user "
            "specifically asks for child-compartment detail.\n"
            "Optional: granularity (DAILY/MONTHLY/HOURLY/TOTAL), "
            "query_type (COST or USAGE; default to COST for spend "
            "questions, USAGE for consumption).\n\n"
            "OUTPUT RULES:\n"
            "Do NOT produce a numerical table or list of per-service or "
            "per-day numbers in your reply. The application renders an "
            "exact table from the raw tool result on its own. Your job "
            "is to give a brief natural-language insight (2-4 sentences) "
            "about what stands out: which service or day dominates, any "
            "obvious trend, anything worth a closer look. If the result "
            "is empty or the call fails, say so plainly - do not invent."
        ),
    )

    # ------------------------------------------------------------------
    # Run the agent.
    # ------------------------------------------------------------------
    question = (
        "Show me my OCI cost for the last 30 days as a daily breakdown by "
        "service. I want to compare it to the OCI Cost Analysis console "
        "with Granularity=Daily, Show=Cost, Group by=Service. After the "
        "table, give me one or two sentences pointing out anything notable."
    )
    print(f"User: {question}\n")

    response = await agent.ainvoke({"messages": [("user", question)]})
    messages = response["messages"]

    # ------------------------------------------------------------------
    # Render deterministic table + CSV from the raw tool output.
    # ------------------------------------------------------------------
    raw_tool_result = find_last_tool_result(messages, "get_summarized_usage")

    print("Daily cost by service (rendered from raw tool result)")
    print("=" * 60)
    if raw_tool_result is None:
        print("(the agent did not call get_summarized_usage)")
    else:
        try:
            parsed = json.loads(raw_tool_result)
            items = extract_items(parsed)
            pivot = build_pivot(items)
            print_daily_service_table(pivot)

            csv_path = Path(__file__).resolve().parent / "oci_daily_cost_agent.csv"
            write_daily_service_csv(pivot, csv_path)
            if pivot is not None:
                print()
                print(f"Wrote CSV: {csv_path.resolve()}")
                print(
                    "Open it in Excel / Google Sheets to compare against "
                    "the OCI Console."
                )
        except (ValueError, TypeError) as exc:
            print(f"(could not parse tool result as JSON: {exc})")
            print(raw_tool_result)
    print()

    # ------------------------------------------------------------------
    # Show the agent's natural-language commentary below the table.
    # ------------------------------------------------------------------
    final_message = messages[-1]
    print("Agent commentary:")
    print("-" * 60)
    print(final_message.content)


if __name__ == "__main__":
    asyncio.run(main())
