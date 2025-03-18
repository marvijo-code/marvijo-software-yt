# Product Context

## Why this project exists
This project aims to create a Model Context Protocol (MCP) server for Azure DevOps Pipelines. The MCP server will provide a standardized interface for interacting with Azure DevOps Pipelines, allowing users to trigger pipeline runs and list available pipelines.

## What problems it solves
- Provides a consistent interface for interacting with Azure DevOps Pipelines
- Simplifies the process of triggering pipeline runs programmatically
- Enables listing available pipelines in a project
- Standardizes authentication with Azure DevOps using tokens

## How it should work
1. The server will authenticate with Azure DevOps using a token stored in environment variables
2. It will connect to a specified Azure DevOps project (also configured via environment variables)
3. It will provide endpoints to:
   - Trigger pipeline runs by name
   - List all available pipelines in the project
4. The server will follow the Model Context Protocol standards as defined in the MCP repository
5. It will run locally using npm
6. It will include comprehensive unit and integration tests 