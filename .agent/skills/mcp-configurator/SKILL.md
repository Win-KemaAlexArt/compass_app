---
name: mcp-configurator
description: Use when you need to add, remove, or modify MCP servers in the project configuration.
---

# MCP Configurator

## Purpose
Manages the lifecycle of MCP (Model Context Protocol) servers for the project, ensuring they are correctly registered in `.gemini/settings.json`.

## Instructions
1. **Read Current Config**: Always check `.gemini/settings.json` first.
2. **Identify Change**: Determine if you need to enable/disable or add a new server.
3. **Update Settings**: Use the `replace` tool to update the `mcp.servers` section in `.gemini/settings.json`.
4. **Verify Health**: Use `run_shell_command` to verify the daemon status or ping relevant endpoints if available.
5. **Document**: Record the change in `docs/decisions.md`.

## Example
**User**: "Add a new MCP server for database management."
**Agent**: [Updates settings.json and records the decision]
