#!/usr/bin/env python3
"""
ComputeID CLI — Command line tool for ComputeID identity management
Every AI agent needs an identity.
"""

import click
import requests
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    from rich.style import Style
    RICH = True
except ImportError:
    RICH = False

API_URL = "https://api.aicomputeid.com"
CONFIG_FILE = Path.home() / ".computeid" / "config.json"

console = Console() if RICH else None

# ── HELPERS ───────────────────────────────────────────────────────────────────

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

def get_token():
    cfg = load_config()
    return cfg.get("token")

def get_api_url():
    cfg = load_config()
    return cfg.get("api_url", API_URL)

def auth_headers():
    token = get_token()
    if not token:
        error("Not logged in. Run: computeid login")
        sys.exit(1)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

def success(msg):
    if RICH:
        console.print(f"[bold green]✓[/bold green] {msg}")
    else:
        print(f"✓ {msg}")

def error(msg):
    if RICH:
        console.print(f"[bold red]✗[/bold red] {msg}")
    else:
        print(f"✗ {msg}")

def info(msg):
    if RICH:
        console.print(f"[bold cyan]→[/bold cyan] {msg}")
    else:
        print(f"→ {msg}")

def warn(msg):
    if RICH:
        console.print(f"[bold yellow]⚠[/bold yellow] {msg}")
    else:
        print(f"⚠ {msg}")

def print_header():
    if RICH:
        console.print()
        console.print(Panel.fit(
            "[bold white]COMPUTE[/bold white][bold cyan]ID[/bold cyan]  [dim]Identity infrastructure for AI agents.[/dim]",
            border_style="cyan",
            padding=(0, 2)
        ))
        console.print()

def fmt_status(status):
    colors = {
        "active":  "[bold green]● active[/bold green]",
        "pending": "[bold yellow]● pending[/bold yellow]",
        "revoked": "[bold red]● revoked[/bold red]",
        "expired": "[bold red]● expired[/bold red]",
    }
    return colors.get(status, status) if RICH else status

def fmt_time(ts):
    try:
        dt = datetime.fromisoformat(ts.replace("Z",""))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return ts or "—"

# ── CLI ROOT ──────────────────────────────────────────────────────────────────

@click.group()
@click.version_option("1.0.1", prog_name="computeid")
def cli():
    """
    ComputeID CLI — Cryptographic identity for AI agents.

    Every AI agent needs an identity.

    Docs: compute-id.com
    """
    pass

# ── STATUS ────────────────────────────────────────────────────────────────────

@cli.command()
def status():
    """Check API health and connection status."""
    print_header()
    api = get_api_url()
    info(f"Connecting to {api}...")
    try:
        r = requests.get(f"{api}/health", timeout=10)
        if r.ok:
            data = r.json()
            success(f"API is online")
            if RICH:
                t = Table(box=box.ROUNDED, border_style="cyan", show_header=False)
                t.add_column("Key", style="bold cyan", width=20)
                t.add_column("Value", style="white")
                t.add_row("API URL", api)
                t.add_row("Status", data.get("status", "running"))
                t.add_row("Time", fmt_time(data.get("time", "")))
                t.add_row("Logged in", "Yes" if get_token() else "No — run: computeid login")
                console.print(t)
            else:
                print(f"  API URL: {api}")
                print(f"  Status: {data.get('status')}")
        else:
            error(f"API returned {r.status_code}")
    except Exception as e:
        error(f"Cannot reach API: {e}")

# ── LOGIN ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--password", "-p", prompt=True, hide_input=True, help="Admin password")
def login(password):
    """Login to ComputeID with your admin password."""
    api = get_api_url()
    try:
        r = requests.post(f"{api}/api/admin/login",
            json={"password": password},
            headers={"Content-Type": "application/json"},
            timeout=10)
        data = r.json()
        if r.ok:
            cfg = load_config()
            cfg["token"] = data["token"]
            cfg["api_url"] = api
            save_config(cfg)
            success("Logged in successfully!")
            info("Token saved to ~/.computeid/config.json")
        else:
            error(f"Login failed: {data.get('error', 'Invalid password')}")
    except Exception as e:
        error(f"Login error: {e}")

@cli.command()
def logout():
    """Logout and clear saved credentials."""
    cfg = load_config()
    cfg.pop("token", None)
    save_config(cfg)
    success("Logged out successfully")

# ── AGENT COMMANDS ────────────────────────────────────────────────────────────

@cli.group()
def agent():
    """Manage AgentPassports for AI agents."""
    pass

@agent.command("list")
@click.option("--status", "-s", default=None, help="Filter by status: active, revoked")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def agent_list(status, as_json):
    """List all registered agent passports."""
    try:
        path = f"{get_api_url()}/v1/agents"
        if status:
            path += f"?status={status}"
        r = requests.get(path, headers=auth_headers(), timeout=10)
        if not r.ok:
            error(f"Failed: {r.json().get('error')}")
            return
        agents = r.json()
        if as_json:
            click.echo(json.dumps(agents, indent=2))
            return
        if not agents:
            warn("No agents found")
            return
        if RICH:
            t = Table(title=f"[bold]Agent Passports ({len(agents)})[/bold]",
                box=box.ROUNDED, border_style="cyan", show_lines=True)
            t.add_column("Passport ID", style="bold cyan", width=14)
            t.add_column("Name", style="white", width=22)
            t.add_column("Organisation", style="dim", width=16)
            t.add_column("Capabilities", style="dim", width=24)
            t.add_column("Status", width=14)
            t.add_column("Issued", width=16)
            for a in agents:
                caps = ", ".join(a.get("capabilities") or [])
                t.add_row(
                    str(a.get("passport_id", "—"))[:12] + "...",
                    a.get("name", "—"),
                    a.get("organization", "—"),
                    caps or "—",
                    fmt_status(a.get("status", "—")),
                    fmt_time(a.get("issued_at", ""))
                )
            console.print(t)
        else:
            print(f"\nAgent Passports ({len(agents)}):")
            for a in agents:
                print(f"  {a.get('passport_id','')[:12]}... | {a.get('name')} | {a.get('status')}")
    except Exception as e:
        error(f"Error: {e}")

@agent.command("issue")
@click.option("--name", "-n", required=True, help="Agent name e.g. 'ResearchAgent'")
@click.option("--org", "-o", default="My Organisation", help="Organisation name")
@click.option("--capabilities", "-c", default="read,web_browse,api_call",
    help="Comma-separated capabilities e.g. read,web_browse,api_call,code_execute")
def agent_issue(name, org, capabilities):
    """Issue a new AgentPassport for an AI agent."""
    caps = [c.strip() for c in capabilities.split(",") if c.strip()]
    info(f"Issuing AgentPassport for {name}...")
    try:
        r = requests.post(f"{get_api_url()}/v1/agents/register",
            json={"name": name, "organization": org, "capabilities": caps},
            headers={"Content-Type": "application/json"},
            timeout=10)
        data = r.json()
        if r.ok:
            success("AgentPassport issued successfully!")
            if RICH:
                t = Table(box=box.ROUNDED, border_style="cyan", show_header=False)
                t.add_column("Key", style="bold cyan", width=22)
                t.add_column("Value", style="white")
                t.add_row("Passport ID", data.get("passport_id", "—"))
                t.add_row("Name", data.get("name", "—"))
                t.add_row("Organisation", data.get("organization", "—"))
                t.add_row("Status", fmt_status(data.get("status", "active")))
                t.add_row("Capabilities", ", ".join(data.get("capabilities", [])))
                t.add_row("Algorithm", data.get("signature_algorithm", "RSA-SHA256"))
                t.add_row("Issued At", fmt_time(data.get("issued_at", "")))
                console.print(t)
                console.print()
                info("Verify with: computeid agent verify " + data.get("passport_id", ""))
            else:
                print(f"  Passport ID: {data.get('passport_id')}")
                print(f"  Status: {data.get('status')}")
                print(f"  Capabilities: {', '.join(data.get('capabilities', []))}")
        else:
            error(f"Failed: {data.get('error')}")
    except Exception as e:
        error(f"Error: {e}")

@agent.command("verify")
@click.argument("passport_id")
def agent_verify(passport_id):
    """Verify an agent passport against the live API."""
    info(f"Verifying passport {passport_id[:12]}...")
    try:
        r = requests.get(f"{get_api_url()}/v1/agents/{passport_id}/verify", timeout=10)
        data = r.json()
        if r.ok:
            status_ok = data.get("status") == "active" and data.get("signature_valid")
            if status_ok:
                success("Passport is valid and active")
            else:
                warn(f"Passport status: {data.get('status')}")
            if RICH:
                t = Table(box=box.ROUNDED, border_style="cyan", show_header=False)
                t.add_column("Key", style="bold cyan", width=22)
                t.add_column("Value", style="white")
                t.add_row("Passport ID", data.get("passport_id", "—"))
                t.add_row("Name", data.get("name", "—"))
                t.add_row("Status", fmt_status(data.get("status", "—")))
                t.add_row("Signature Valid", str(data.get("signature_valid", False)))
                t.add_row("Algorithm", data.get("signature_algorithm", "—"))
                t.add_row("Capabilities", ", ".join(data.get("capabilities", [])))
                t.add_row("Issued At", fmt_time(data.get("issued_at", "")))
                if data.get("revoked_at"):
                    t.add_row("Revoked At", fmt_time(data.get("revoked_at", "")))
                console.print(t)
            else:
                print(f"  Status: {data.get('status')}")
                print(f"  Signature Valid: {data.get('signature_valid')}")
        else:
            error(f"Verification failed: {data.get('error')}")
    except Exception as e:
        error(f"Error: {e}")

@agent.command("check")
@click.argument("passport_id")
@click.argument("capability")
def agent_check(passport_id, capability):
    """Check whether an agent has a specific capability."""
    try:
        r = requests.get(
            f"{get_api_url()}/v1/agents/{passport_id}/capabilities/{capability}",
            timeout=10)
        data = r.json()
        if data.get("granted"):
            success(f"Capability '{capability}' is GRANTED")
            if RICH:
                console.print(f"  [dim]Bound at: {fmt_time(data.get('bound_at',''))}[/dim]")
        else:
            warn(f"Capability '{capability}' is DENIED — reason: {data.get('reason','unknown')}")
    except Exception as e:
        error(f"Error: {e}")

@agent.command("log")
@click.argument("passport_id")
@click.option("--action", "-a", required=True, help="Action taken e.g. 'web_search'")
@click.option("--outcome", "-o", default="success",
    type=click.Choice(["success", "failure", "partial"]),
    help="Outcome of the action")
def agent_log(passport_id, action, outcome):
    """Log an action to an agent's audit trail."""
    try:
        r = requests.post(f"{get_api_url()}/v1/agents/{passport_id}/actions",
            json={"action": action, "outcome": outcome},
            headers={"Content-Type": "application/json"},
            timeout=10)
        data = r.json()
        if r.ok:
            success(f"Action '{action}' logged (log ID: {data.get('log_id','')})")
        else:
            error(f"Failed: {data.get('error')}")
    except Exception as e:
        error(f"Error: {e}")

@agent.command("audit")
@click.argument("passport_id")
@click.option("--limit", "-l", default=20, help="Number of entries to show")
def agent_audit(passport_id, limit):
    """View the audit trail for an agent."""
    try:
        r = requests.get(
            f"{get_api_url()}/v1/agents/{passport_id}/actions?limit={limit}",
            timeout=10)
        entries = r.json()
        if not entries:
            warn("No audit entries found for this agent")
            return
        if RICH:
            t = Table(title=f"[bold]Audit Trail ({len(entries)})[/bold]",
                box=box.ROUNDED, border_style="cyan", show_lines=True)
            t.add_column("Time", style="dim", width=16)
            t.add_column("Action", style="white", width=22)
            t.add_column("Outcome", width=12)
            for e in entries:
                s = e.get("outcome", "")
                sc = "[green]success[/green]" if s == "success" else f"[red]{s}[/red]"
                t.add_row(fmt_time(e.get("logged_at", "")), e.get("action", "—"), sc)
            console.print(t)
        else:
            for e in entries:
                print(f"  {fmt_time(e.get('logged_at',''))} | {e.get('action')} | {e.get('outcome')}")
    except Exception as e:
        error(f"Error: {e}")

@agent.command("revoke")
@click.argument("passport_id")
@click.option("--reason", "-r", default="manual_revocation", help="Reason for revocation")
@click.option("--force", is_flag=True, help="Skip confirmation")
def agent_revoke(passport_id, reason, force):
    """Revoke an agent passport immediately."""
    if not force:
        click.confirm(f"Revoke passport {passport_id[:12]}...? This cannot be undone.", abort=True)
    try:
        r = requests.delete(f"{get_api_url()}/v1/agents/{passport_id}/revoke",
            json={"reason": reason},
            headers={"Content-Type": "application/json"},
            timeout=10)
        data = r.json()
        if r.ok:
            success(f"Passport revoked. Status: {data.get('status')}")
            info(f"Revoked at: {fmt_time(data.get('revoked_at',''))}")
        else:
            error(f"Failed: {data.get('error')}")
    except Exception as e:
        error(f"Error: {e}")

# ── LOGS ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--limit", "-l", default=20, help="Number of log entries to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def logs(limit, as_json):
    """View organisation-wide audit logs."""
    try:
        r = requests.get(f"{get_api_url()}/api/logs", headers=auth_headers(), timeout=10)
        if not r.ok:
            error(f"Failed: {r.json().get('error')}")
            return
        entries = r.json()[:limit]
        if as_json:
            click.echo(json.dumps(entries, indent=2))
            return
        if not entries:
            warn("No audit logs found")
            return
        if RICH:
            t = Table(title=f"[bold]Audit Logs (last {len(entries)})[/bold]",
                box=box.ROUNDED, border_style="cyan", show_lines=True)
            t.add_column("Time", style="dim", width=16)
            t.add_column("Action", style="white", width=22)
            t.add_column("Status", width=12)
            for e in entries:
                action = e.get("action","").replace("_"," ").title()
                s = e.get("status","")
                sc = "[green]success[/green]" if s=="success" else "[red]denied[/red]" if s=="denied" else f"[yellow]{s}[/yellow]"
                t.add_row(fmt_time(e.get("created_at","")), action, sc)
            console.print(t)
        else:
            print(f"\nAudit Logs ({len(entries)}):")
            for e in entries:
                print(f"  {fmt_time(e.get('created_at',''))} | {e.get('action')} | {e.get('status')}")
    except Exception as e:
        error(f"Error: {e}")

# ── CONFIG ────────────────────────────────────────────────────────────────────

@cli.group()
def config():
    """Manage CLI configuration."""
    pass

@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = load_config()
    if RICH:
        t = Table(box=box.ROUNDED, border_style="cyan", show_header=False)
        t.add_column("Key", style="bold cyan", width=20)
        t.add_column("Value", style="white")
        t.add_row("API URL", cfg.get("api_url", API_URL))
        t.add_row("Logged In", "Yes ✓" if cfg.get("token") else "No")
        t.add_row("Config File", str(CONFIG_FILE))
        console.print(t)
    else:
        print(f"API URL: {cfg.get('api_url', API_URL)}")
        print(f"Logged in: {'Yes' if cfg.get('token') else 'No'}")

@config.command("set-url")
@click.argument("url")
def config_set_url(url):
    """Set a custom API URL (for self-hosted ComputeID)."""
    cfg = load_config()
    cfg["api_url"] = url
    save_config(cfg)
    success(f"API URL set to {url}")

# ── QUICK START ───────────────────────────────────────────────────────────────

@cli.command()
def quickstart():
    """Interactive quickstart guide."""
    print_header()
    if RICH:
        steps = [
            ("1", "Login",              "computeid login"),
            ("2", "Check status",       "computeid status"),
            ("3", "Issue a passport",   "computeid agent issue --name 'MyAgent' --org 'Acme Corp'"),
            ("4", "Verify passport",    "computeid agent verify <passport_id>"),
            ("5", "Check capability",   "computeid agent check <passport_id> web_browse"),
            ("6", "Log an action",      "computeid agent log <passport_id> --action web_search"),
            ("7", "View audit trail",   "computeid agent audit <passport_id>"),
            ("8", "Revoke passport",    "computeid agent revoke <passport_id> --reason 'done'"),
            ("9", "View org logs",      "computeid logs"),
        ]
        t = Table(title="[bold]ComputeID CLI Quick Start[/bold]",
            box=box.ROUNDED, border_style="cyan")
        t.add_column("Step", style="bold cyan", width=6)
        t.add_column("Action", style="white", width=22)
        t.add_column("Command", style="bold green", width=60)
        for step, action, cmd in steps:
            t.add_row(step, action, cmd)
        console.print(t)
        console.print()
        console.print("[dim]Docs: compute-id.com  |  praveen.gajjala@compute-id.com[/dim]")
    else:
        print("ComputeID CLI Quick Start:")
        print("  1. computeid login")
        print("  2. computeid status")
        print("  3. computeid agent issue --name 'MyAgent' --org 'Acme Corp'")
        print("  4. computeid agent verify <passport_id>")
        print("  5. computeid agent check <passport_id> web_browse")
        print("  6. computeid agent log <passport_id> --action web_search")
        print("  7. computeid agent revoke <passport_id>")

if __name__ == "__main__":
    cli()
