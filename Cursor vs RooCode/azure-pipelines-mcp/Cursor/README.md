# Azure DevOps Pipelines MCP Server

A Model Context Protocol (MCP) server for Azure DevOps Pipelines. This server provides a standardized interface for interacting with Azure DevOps Pipelines, allowing you to trigger pipeline runs and list available pipelines.

## Features

- Authenticate with Azure DevOps using a token
- Connect to a specified Azure DevOps project
- Trigger pipeline runs by name
- List all available pipelines in the project

## Prerequisites

- Node.js (v14 or higher)
- npm
- Azure DevOps account with appropriate permissions
- Personal Access Token (PAT) with appropriate permissions

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd azure-pipelines-mcp
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file based on the `.env.example` file:
   ```bash
   cp .env.example .env
   ```

4. Update the `.env` file with your Azure DevOps credentials:
   ```
   AZURE_DEVOPS_TOKEN=your_personal_access_token
   AZURE_DEVOPS_ORGANIZATION=your_organization_name
   AZURE_DEVOPS_PROJECT=your_project_name
   PORT=3000
   ```

## Usage

### Start the server

```bash
npm start
```

For development with auto-reload:

```bash
npm run dev
```

### API Endpoints

#### List Pipelines

```
GET /pipelines
```

Response:
```json
{
  "pipelines": [
    {
      "id": "1",
      "name": "Pipeline 1",
      "url": "https://dev.azure.com/organization/project/_build?definitionId=1"
    },
    {
      "id": "2",
      "name": "Pipeline 2",
      "url": "https://dev.azure.com/organization/project/_build?definitionId=2"
    }
  ]
}
```

#### Trigger Pipeline Run

```
POST /pipelines/run
```

Request Body:
```json
{
  "pipelineName": "Pipeline 1"
}
```

Response:
```json
{
  "id": "1",
  "name": "Pipeline 1",
  "status": "queued",
  "url": "https://dev.azure.com/organization/project/_build/results?buildId=123"
}
```

## Testing

Run all tests:

```bash
npm test
```

Run unit tests:

```bash
npm run test:unit
```

Run integration tests:

```bash
npm run test:integration
```

## License

ISC

## References

- [Model Context Protocol (MCP) Repository](https://github.com/modelcontextprotocol/servers)
- [Azure DevOps REST API Documentation](https://docs.microsoft.com/en-us/rest/api/azure/devops/?view=azure-devops-rest-7.1) 