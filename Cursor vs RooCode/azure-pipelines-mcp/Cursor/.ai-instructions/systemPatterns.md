# System Patterns

## How the system is built
The system will be built as a Node.js application following the Model Context Protocol (MCP) standards. It will use Express.js for the HTTP server and will interact with the Azure DevOps REST API.

## Key technical decisions
- **Node.js and Express**: For the server implementation
- **Axios**: For making HTTP requests to the Azure DevOps API
- **Dotenv**: For managing environment variables
- **Jest**: For unit and integration testing
- **MCP Standards**: Following the Model Context Protocol for server implementation

## Architecture patterns
- **MVC Pattern**: Separating the concerns of the application
  - Models: Representing the data structures
  - Controllers: Handling the business logic
  - Routes: Defining the API endpoints
- **Repository Pattern**: For abstracting the data access layer
- **Dependency Injection**: For better testability
- **Environment Configuration**: Using environment variables for configuration
- **Error Handling Middleware**: For consistent error responses 