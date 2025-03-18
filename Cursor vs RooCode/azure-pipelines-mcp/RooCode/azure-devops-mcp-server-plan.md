# Azure DevOps MCP Server Plan

## Overview

We will build a Node.js MCP server written in plain JavaScript (ES Modules) that connects to Azure DevOps and supports triggering pipeline runs and listing pipelines.

### Objectives
- **Authenticate with Azure DevOps** using a Personal Access Token (PAT).
- **Use separate environment variables**:
  - `AZURE_DEVOPS_TOKEN` for authentication,
  - `AZURE_DEVOPS_ORG` for the Azure DevOps organization,
  - `AZURE_DEVOPS_PROJECT` for the project name.
- **Provide two MCP tools**:
  - `list_pipelines`: Lists all pipelines in the project via a GET request.
  - `trigger_pipeline`: Triggers a pipeline run by finding the pipeline by its name and sending a POST request.
- **Local Execution** via npm.
- **Testing Strategy** with both unit tests and integration tests.

## Detailed Implementation Plan

```mermaid
flowchart TD
   A[Start: Initialize server]
   B[Check env variables: AZURE_DEVOPS_TOKEN, AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT]
   C[Setup Axios instance with PAT-based authentication]
   D[List Pipelines Function: GET request to Azure DevOps API]
   E[Trigger Pipeline Function: Lookup pipeline by name & POST request to trigger run]
   F[Define MCP Server using the SDK]
   G[Set Tool Handlers for "list_pipelines" and "trigger_pipeline"]
   H[Run MCP server via StdioServerTransport]
   I[Write Unit Tests (using Jest, mock Axios)]
   J[Write Integration Tests (using Jest with Nock to simulate API responses)]
   K[Package and run server locally via npm scripts]
   
   A --> B 
   B --> C
   C --> D
   C --> E
   D --> F
   E --> F
   F --> G
   G --> H
   H --> K
   K --> I
   I --> J
```

## Project Structure

```
azure-devops-mcp-server/
├── package.json         # Contains npm scripts, dependencies (Axios, MCP SDK, Jest, Nock)
├── index.js             # Main server file implementing MCP tools
└── test/
    ├── unit/
    │   └── azureDevOpsServer.test.js         # Unit tests for business logic (mocking Axios)
    └── integration/
        └── azureDevOpsServer.integration.test.js  # Integration tests for MCP endpoints using Nock
```

## Server Setup Details

1. **Environment Variables**:  
   The server will read:
   - `AZURE_DEVOPS_TOKEN`
   - `AZURE_DEVOPS_ORG`
   - `AZURE_DEVOPS_PROJECT`

2. **MCP Tools**:  
   - **list_pipelines**: Executes a GET request to the Azure DevOps REST API to retrieve pipelines.
   - **trigger_pipeline**: Accepts a pipeline name (and optional variables) to send a trigger run POST request.

3. **Technology Stack**:  
   - Node.js (ES Modules)
   - MCP Server SDK
   - Axios for HTTP requests
   - Jest for testing
   - Nock for HTTP interception in integration tests

4. **Running Locally**:  
   The server will be executable via npm scripts. For example, `"start": "node index.js"`.

## Testing Strategy

- **Unit Tests**:  
  Use Jest and mocking of Axios to assert that functions for listing and triggering pipelines work correctly.

- **Integration Tests**:  
  Use Jest with Nock to simulate responses from Azure DevOps APIs and test the MCP endpoint functionality end-to-end.

## Conclusion

This plan adheres to industry standards and best practices. It sets a clear direction for building, testing, and deploying the MCP server locally.