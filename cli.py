#!/usr/bin/env python3
"""
ComputeID CLI — Command line tool for ComputeID identity management
Every GPU needs a passport. Every AI agent needs an identity.
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
            "[bold white]COMPUTE[/bold white][bold cyan]ID[/bold cyan]  [dim]Every GPU needs a passport. We issue them.[/dim]",
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
@click.version_option("1.0.0", prog_name="computeid")
def cli():
    """
    ComputeID CLI — Cryptographic identity for AI compute infrastructure.

    Every GPU needs a passport. Every AI agent needs an identity.

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

# ── DEVICE COMMANDS ───────────────────────────────────────────────────────────

@cli.group()
def device():
    """Manage DevicePassports for GPUs and servers."""
    pass

@device.command("list")
@click.option("--status", "-s", default=None, help="Filter by status: active, pending, revoked")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def device_list(status, as_json):
    """List all registered devices."""
    try:
        r = requests.get(f"{get_api_url()}/api/devices", headers=auth_headers(), timeout=10)
        if not r.ok:
            error(f"Failed to fetch devices: {r.json().get('error')}")
            return
        devices = r.json()
        if status:
            devices = [d for d in devices if d.get("status") == status]
        if as_json:
            click.echo(json.dumps(devices, indent=2))
            return
        if not devices:
            warn("No devices found")
            return
        if RICH:
            t = Table(title=f"[bold]Devices ({len(devices)})[/bold]",
                box=box.ROUNDED, border_style="cyan", show_lines=True)
            t.add_column("Code", style="bold cyan", width=12)
            t.add_column("Name", style="white", width=22)
            t.add_column("Type", style="dim", width=10)
            t.add_column("IP Address", style="dim", width=16)
            t.add_column("Status", width=14)
            t.add_column("Certificate", width=12)
            t.add_column("Registered", width=16)
            for d in devices:
                t.add_row(
                    d.get("device_code", "—"),
                    d.get("name", "—"),
                    d.get("type", "—"),
                    d.get("ip_address", "—"),
                    fmt_status(d.get("status", "—")),
                    "[green]✓ Issued[/green]" if d.get("public_key") else "[dim]None[/dim]",
                    fmt_time(d.get("created_at", ""))
                )
            console.print(t)
        else:
            print(f"\nDevices ({len(devices)}):")
            for d in devices:
                print(f"  {d.get('device_code')} | {d.get('name')} | {d.get('status')} | {d.get('ip_address')}")
    except Exception as e:
        error(f"Error: {e}")

@device.command("register")
@click.option("--name", "-n", required=True, help="Device name e.g. 'NVIDIA A100'")
@click.option("--ip", "-i", required=True, help="Device IP address")
@click.option("--type", "-t", "dtype", default="GPU",
    type=click.Choice(["GPU","Server","TPU","FPGA"], case_sensitive=False),
    help="Device type")
def device_register(name, ip, dtype):
    """Register a new device and issue a DevicePassport."""
    info(f"Registering {dtype}: {name} ({ip})...")
    try:
        r = requests.post(f"{get_api_url()}/api/devices/register",
            json={"name": name, "type": dtype, "ip_address": ip},
            headers={"Content-Type": "application/json"},
            timeout=10)
        data = r.json()
        if r.ok:
            success(f"Device registered successfully!")
            if RICH:
                t = Table(box=box.ROUNDED, border_style="green", show_header=False)
                t.add_column("Key", style="bold cyan", width=20)
                t.add_column("Value", style="white")
                t.add_row("Device Code", data.get("device_code", "—"))
                t.add_row("Name", data.get("name", "—"))
                t.add_row("Type", data.get("type", "—"))
                t.add_row("IP Address", data.get("ip_address", "—"))
                t.add_row("Status", fmt_status(data.get("status", "pending")))
                t.add_row("Certificate", "✓ Issued" if data.get("public_key") else "Pending approval")
                console.print(t)
                console.print()
                warn("Device is pending admin approval. Run: computeid device approve " + data.get("device_code",""))
            else:
                print(f"  Code: {data.get('device_code')}")
                print(f"  Status: pending — awaiting admin approval")
        else:
            error(f"Registration failed: {data.get('error')}")
    except Exception as e:
        error(f"Error: {e}")

@device.command("approve")
@click.argument("device_id")
def device_approve(device_id):
    """Approve a pending device."""
    info(f"Approving device {device_id}...")
    try:
        r = requests.patch(f"{get_api_url()}/api/devices/{device_id}/approve",
            headers=auth_headers(), timeout=10)
        if r.ok:
            success(f"Device {device_id} approved and activated!")
        else:
            error(f"Failed: {r.json().get('error')}")
    except Exception as e:
        error(f"Error: {e}")

@device.command("revoke")
@click.argument("device_id")
@click.option("--force", is_flag=True, help="Skip confirmation")
def device_revoke(device_id, force):
    """Revoke a device certificate immediately."""
    if not force:
        click.confirm(f"Revoke device {device_id}? This removes all access immediately.", abort=True)
    info(f"Revoking device {device_id}...")
    try:
        r = requests.patch(f"{get_api_url()}/api/devices/{device_id}/revoke",
            headers=auth_headers(), timeout=10)
        if r.ok:
            success(f"Device {device_id} revoked. Access removed immediately.")
        else:
            error(f"Failed: {r.json().get('error')}")
    except Exception as e:
        error(f"Error: {e}")

@device.command("authenticate")
@click.argument("device_code")
def device_authenticate(device_code):
    """Authenticate a device and get a JWT token."""
    info(f"Authenticating device {device_code}...")
    try:
        r = requests.post(f"{get_api_url()}/api/devices/authenticate",
            json={"device_code": device_code},
            headers={"Content-Type": "application/json"},
            timeout=10)
        data = r.json()
        if r.ok:
            success("Device authenticated!")
            token = data.get("access_token", "")
            if RICH:
                console.print(f"\n[bold cyan]Access Token:[/bold cyan]")
                console.print(f"[dim]{token[:60]}...[/dim]")
                console.print(f"\n[dim]Valid for 1 hour. Use in Authorization: Bearer header.[/dim]")
            else:
                print(f"Token: {token[:60]}...")
        else:
            error(f"Authentication failed: {data.get('error')}")
    except Exception as e:
        error(f"Error: {e}")

# ── AGENT COMMANDS ────────────────────────────────────────────────────────────

@cli.group()
def agent():
    """Manage AgentPassports for AI agents."""
    pass

@agent.command("issue")
@click.option("--name", "-n", required=True, help="Agent name e.g. 'ResearchAgent'")
@click.option("--org", "-o", default="My Organisation", help="Organisation name")
@click.option("--email", "-e", default="admin@compute-id.com", help="Owner email")
@click.option("--trust", "-t", default="standard",
    type=click.Choice(["restricted","standard","elevated","autonomous"], case_sensitive=False),
    help="Trust level")
@click.option("--model", "-m", default="unknown", help="AI model e.g. claude-sonnet-4-5")
def agent_issue(name, org, email, trust, model):
    """Issue a new AgentPassport for an AI agent."""
    try:
        from computeid import issue_agent_passport
        info(f"Issuing AgentPassport for {name}...")
        passport = issue_agent_passport(
            agent_name=name,
            owner_org=org,
            owner_email=email,
            trust_level=trust,
            model=model
        )
        success(f"AgentPassport issued successfully!")
        if RICH:
            t = Table(box=box.ROUNDED, border_style="cyan", show_header=False)
            t.add_column("Key", style="bold cyan", width=20)
            t.add_column("Value", style="white")
            t.add_row("Agent ID", passport.agent_id[:16] + "...")
            t.add_row("Name", passport.agent_name)
            t.add_row("Organisation", passport.owner_org)
            t.add_row("Trust Level", trust)
            t.add_row("Model", model)
            t.add_row("Status", fmt_status(passport.status))
            t.add_row("Fingerprint", passport._fingerprint)
            t.add_row("Issued At", fmt_time(passport.issued_at))
            t.add_row("Expires At", fmt_time(passport.expires_at))
            console.print(t)
            console.print()
            info("Export passport with: computeid agent export --id " + passport.agent_id[:8])
        else:
            print(f"  ID: {passport.agent_id[:16]}...")
            print(f"  Trust: {trust}")
            print(f"  Status: {passport.status}")
    except ImportError:
        error("computeid-sdk not installed. Run: pip install computeid-sdk")
    except Exception as e:
        error(f"Error: {e}")

# ── LOGS ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--limit", "-l", default=20, help="Number of log entries to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def logs(limit, as_json):
    """View audit logs."""
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
            t.add_column("Device ID", style="cyan", width=14)
            t.add_column("Action", style="white", width=22)
            t.add_column("Status", width=12)
            t.add_column("IP", style="dim", width=16)
            for e in entries:
                action = e.get("action","").replace("_"," ").title()
                s = e.get("status","")
                sc = "[green]success[/green]" if s=="success" else "[red]denied[/red]" if s=="denied" else f"[yellow]{s}[/yellow]"
                t.add_row(
                    fmt_time(e.get("created_at","")),
                    (e.get("device_id","") or "")[:10]+"...",
                    action,
                    sc,
                    e.get("ip_address","—") or "—"
                )
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
            ("1", "Login", "computeid login"),
            ("2", "Check status", "computeid status"),
            ("3", "Register a GPU", "computeid device register --name 'NVIDIA A100' --ip 192.168.1.10"),
            ("4", "List devices", "computeid device list"),
            ("5", "Issue agent passport", "computeid agent issue --name 'MyAgent' --trust standard"),
            ("6", "View audit logs", "computeid logs"),
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
        console.print("[dim]Docs: compute-id.com  |  hello@compute-id.com[/dim]")
    else:
        print("ComputeID CLI Quick Start:")
        print("  1. computeid login")
        print("  2. computeid status")
        print("  3. computeid device register --name 'NVIDIA A100' --ip 192.168.1.10")
        print("  4. computeid device list")
        print("  5. computeid agent issue --name 'MyAgent' --trust standard")
        print("  6. computeid logs")

if __name__ == "__main__":
    cli()
