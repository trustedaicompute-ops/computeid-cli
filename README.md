# ComputeID CLI

Command line tool for ComputeID — cryptographic identity for AI compute infrastructure.

## Install

```bash
pip install computeid-cli
```

## Quick Start

```bash
# Save your API key (checked against the API; stored in ~/.computeid/config.json, mode 600)
computeid login
# ...or skip login and set it in the environment
export COMPUTEID_API_KEY=your-api-key

# Check status
computeid status

# Issue an agent passport
computeid agent issue --name "ResearchAgent" --org "Acme Corp" --capabilities read,web_browse

# List, verify, check a capability, revoke
computeid agent list
computeid agent verify <passport_id>
computeid agent check <passport_id> web_browse
computeid agent revoke <passport_id> --reason "done"

# View audit logs
computeid logs

# Get help
computeid --help
```

## Commands

| Command | Description |
|---------|-------------|
| `computeid status` | Check API health |
| `computeid login` | Save your API key (sent as `X-API-Key`) |
| `computeid logout` | Remove the saved API key |
| `computeid agent list` | List your AgentPassports |
| `computeid agent issue` | Issue an AgentPassport |
| `computeid agent verify` | Verify a passport (public, no key needed) |
| `computeid agent check` | Check a passport's capability |
| `computeid agent log` | Log an agent action |
| `computeid agent audit` | View an agent's action log |
| `computeid agent revoke` | Revoke a passport |
| `computeid logs` | View your account's audit logs |
| `computeid config show` | Show configuration |
| `computeid config set-url` | Point the CLI at another API URL |
| `computeid quickstart` | Interactive quick start guide |

`COMPUTEID_API_KEY`, when set, takes precedence over the saved key.

## Docs

compute-id.com | hello@compute-id.com
