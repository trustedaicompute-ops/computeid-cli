# ComputeID CLI

Command line tool for ComputeID — cryptographic identity for AI compute infrastructure.

## Install

```bash
pip install computeid-cli
```

## Quick Start

```bash
# Login
computeid login

# Check status
computeid status

# Register a GPU
computeid device register --name "NVIDIA A100" --ip 192.168.1.10

# List devices
computeid device list

# Approve a device
computeid device approve GPU-001

# Revoke a device
computeid device revoke GPU-001

# Issue an agent passport
computeid agent issue --name "ResearchAgent" --trust standard

# View audit logs
computeid logs

# Get help
computeid --help
```

## Commands

| Command | Description |
|---------|-------------|
| `computeid status` | Check API health |
| `computeid login` | Login with admin password |
| `computeid logout` | Logout |
| `computeid device list` | List all devices |
| `computeid device register` | Register a new GPU or server |
| `computeid device approve` | Approve a pending device |
| `computeid device revoke` | Revoke a device certificate |
| `computeid device authenticate` | Get JWT token for a device |
| `computeid agent issue` | Issue an AgentPassport |
| `computeid logs` | View audit logs |
| `computeid config show` | Show configuration |
| `computeid quickstart` | Interactive quick start guide |

## Docs

compute-id.com | hello@compute-id.com
