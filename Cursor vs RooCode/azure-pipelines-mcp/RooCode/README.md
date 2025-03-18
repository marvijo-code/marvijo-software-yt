# Azure DevOps MCP Server

A Model Context Protocol (MCP) server for interacting with Azure DevOps Pipelines. This server provides tools for listing pipelines and triggering pipeline runs.

## Features

- **List Pipelines**: Get a list of all pipelines in your Azure DevOps project
- **Trigger Pipeline Runs**: Trigger a pipeline run by name with optional variables
- **MCP Integration**: Seamlessly integrates with MCP-enabled applications

## Prerequisites

- Node.js v14 or higher
- npm v6 or higher
- Azure DevOps Personal Access Token (PAT) with appropriate permissions:
  - Read access to pipelines for listing
  - Execute access to pipelines for triggering runs

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/azure-devops-mcp-server.git
   cd azure-devops-mcp-server
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Configuration

The server requires the following environment variables:

- `AZURE_DEVOPS_TOKEN`: Your Azure DevOps Personal Access Token
- `AZURE_DEVOPS_ORG`: Your Azure DevOps organization name
- `AZURE_DEVOPS_PROJECT`: Your Azure DevOps project name

You can set these environment variables in your shell or create a `.env` file (requires dotenv package).

Example `.env` file:
```
AZURE_DEVOPS_TOKEN=your_personal_access_token
AZURE_DEVOPS_ORG=your_organization
AZURE_DEVOPS_PROJECT=your_project
```

## Usage

### Starting the Server

```bash
npm start
```

The server will start and listen for MCP requests via stdio.

### MCP Tools

The server provides the following MCP tools:

#### list_pipelines

Lists all pipelines in the specified Azure DevOps project.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Example Response:**
```json
[
  {
    "id": 1,
    "name": "Build Pipeline",
    "url": "https://dev.azure.com/org/project/_apis/pipelines/1"
  },
  {
    "id": 2,
    "name": "Deploy Pipeline",
    "url": "https://dev.azure.com/org/project/_apis/pipelines/2"
  }
]
```

#### trigger_pipeline

Triggers a pipeline run by name.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Name of the pipeline to trigger"
    },
    "variables": {
      "type": "object",
      "description": "Optional variables to pass to the pipeline",
      "additionalProperties": {
        "type": "string"
      }
    }
  },
  "required": ["name"]
}
```

**Example Input:**
```json
{
  "name": "Build Pipeline",
  "variables": {
    "environment": "production",
    "debug": "false"
  }
}
```

**Example Response:**
```json
{
  "id": 123,
  "name": "Build Pipeline",
  "status": "queued",
  "url": "https://dev.azure.com/org/project/_build/results?buildId=123"
}
```

## MCP Configuration

To use this server with an MCP client, add it to your MCP configuration file:

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "node",
      "args": ["/path/to/azure-devops-mcp-server/index.js"],
      "env": {
        "AZURE_DEVOPS_TOKEN": "your_personal_access_token",
        "AZURE_DEVOPS_ORG": "your_organization",
        "AZURE_DEVOPS_PROJECT": "your_project"
      }
    }
  }
}
```

## Development

### Running Tests

Run unit tests:
```bash
npm run test:unit
```

Run integration tests:
```bash
npm run test:integration
```

Run all tests:
```bash
npm test
```

### Project Structure

- `index.js`: Main server file
- `test/unit/`: Unit tests
- `test/integration/`: Integration tests

## License

MIT