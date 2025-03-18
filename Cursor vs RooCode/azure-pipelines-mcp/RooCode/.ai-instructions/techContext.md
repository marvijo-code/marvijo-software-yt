# Tech Context: Azure DevOps MCP Server

## Technologies used
- **Node.js**: Runtime environment for executing JavaScript code server-side
- **JavaScript (ES Modules)**: Programming language with modern ES module syntax
- **MCP Server SDK**: Official SDK for implementing Model Context Protocol servers
- **Axios**: Promise-based HTTP client for making requests to the Azure DevOps API
- **Jest**: JavaScript testing framework for unit and integration tests
- **Nock**: HTTP server mocking and expectations library for testing HTTP requests

## Development setup
- **Node.js Environment**: Requires Node.js v14+ installed
- **npm**: Package manager for installing dependencies
- **Environment Variables**:
  - `AZURE_DEVOPS_TOKEN`: Personal Access Token (PAT) for Azure DevOps authentication
  - `AZURE_DEVOPS_ORG`: Azure DevOps organization name
  - `AZURE_DEVOPS_PROJECT`: Azure DevOps project name
- **Development Workflow**:
  1. Clone the repository
  2. Install dependencies with `npm install`
  3. Set up environment variables
  4. Run tests with `npm test`
  5. Start the server with `npm start`

## Technical constraints
- **Authentication**: Requires a valid Azure DevOps Personal Access Token (PAT) with appropriate permissions:
  - Read access to pipelines for listing
  - Execute access to pipelines for triggering runs
- **API Limitations**:
  - Subject to Azure DevOps API rate limits
  - Dependent on Azure DevOps API availability
- **Environment Requirements**:
  - Node.js v14 or higher
  - npm v6 or higher
- **MCP Protocol Constraints**:
  - Communication via stdio only
  - Limited to the capabilities defined by the MCP protocol
- **Security Considerations**:
  - PAT token must be kept secure and not committed to version control
  - Environment variables should be properly managed in production environments