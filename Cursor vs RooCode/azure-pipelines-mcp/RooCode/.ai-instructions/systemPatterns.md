# System Patterns: Azure DevOps MCP Server

## How the system is built
The Azure DevOps MCP server is built as a Node.js application using the Model Context Protocol (MCP) Server SDK. It follows a modular architecture with clear separation of concerns:

1. **Core Server Logic**: Handles MCP protocol communication and tool registration
2. **Azure DevOps API Client**: Manages HTTP requests to the Azure DevOps REST API
3. **Tool Handlers**: Implements the specific functionality for each MCP tool
4. **Error Handling**: Provides consistent error responses and logging

The system uses a stdio-based transport mechanism provided by the MCP SDK to communicate with clients.

## Key technical decisions
1. **Plain JavaScript with ES Modules**: Using modern JavaScript with ES Modules syntax for better code organization and compatibility.
2. **Axios for HTTP Requests**: Chosen for its simplicity, promise-based API, and wide adoption in the JavaScript ecosystem.
3. **Environment Variables for Configuration**: Using environment variables for sensitive information (token) and configuration (org, project) to keep these values out of the codebase.
4. **MCP Server SDK**: Leveraging the official SDK to ensure compatibility with the MCP protocol.
5. **Jest for Testing**: Using Jest as the testing framework for both unit and integration tests due to its comprehensive feature set.
6. **Nock for HTTP Mocking**: Using Nock to intercept and mock HTTP requests during testing to avoid actual API calls.

## Architecture patterns
1. **Dependency Injection**: The server components are designed with dependency injection in mind, making them easier to test and maintain.
2. **Adapter Pattern**: The Azure DevOps API client acts as an adapter between the MCP tools and the Azure DevOps REST API.
3. **Command Pattern**: Each MCP tool implements a specific command that can be executed by the server.
4. **Error Handling Middleware**: Consistent error handling throughout the application.
5. **Configuration Management**: Using environment variables for configuration to keep sensitive information secure.
6. **Testing Pyramid**: Following the testing pyramid with more unit tests than integration tests.