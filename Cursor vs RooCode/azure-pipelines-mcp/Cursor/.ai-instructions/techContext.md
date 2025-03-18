# Tech Context

## Technologies used
- **Node.js**: JavaScript runtime
- **Express.js**: Web framework for Node.js
- **Axios**: HTTP client for making API requests
- **Dotenv**: Environment variable management
- **Jest**: Testing framework
- **Supertest**: HTTP testing library
- **ESLint**: Code linting
- **Prettier**: Code formatting
- **Azure DevOps REST API**: For interacting with Azure DevOps Pipelines

## Development setup
- Node.js environment
- npm for package management
- Environment variables for configuration:
  - `AZURE_DEVOPS_TOKEN`: Personal Access Token for Azure DevOps
  - `AZURE_DEVOPS_ORGANIZATION`: Azure DevOps organization name
  - `AZURE_DEVOPS_PROJECT`: Azure DevOps project name
  - `PORT`: Port for the MCP server (default: 3000)

## Technical constraints
- Must follow the Model Context Protocol standards
- Must authenticate with Azure DevOps using a token
- Must run locally via npm
- Must provide specific endpoints for Azure DevOps Pipelines operations
- Must include comprehensive tests 