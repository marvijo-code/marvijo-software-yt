# Active Context: Azure DevOps MCP Server

## What you're working on now
- Completed the implementation of an MCP server for Azure DevOps Pipelines
- Implemented two main tools:
  1. `list_pipelines`: Lists all pipelines in a specified Azure DevOps project
  2. `trigger_pipeline`: Triggers a pipeline run by name
- Set up the project structure with proper testing
- Created comprehensive documentation

## Recent changes
- Created the project structure with all necessary files:
  - `index.js`: Main server implementation
  - `package.json`: Project configuration and dependencies
  - `jest.config.js`: Testing configuration
  - `.gitignore`: Git ignore rules
  - `README.md`: Project documentation
- Implemented the AzureDevOpsClient class for interacting with the Azure DevOps API
- Implemented the AzureDevOpsMcpServer class for handling MCP requests
- Created unit tests for the AzureDevOpsClient class
- Created integration tests for the MCP server
- Set up environment variable validation for:
  - `AZURE_DEVOPS_TOKEN`
  - `AZURE_DEVOPS_ORG`
  - `AZURE_DEVOPS_PROJECT`

## Next steps
1. Install dependencies:
   ```bash
   npm install
   ```

2. Run tests to verify the implementation:
   ```bash
   npm test
   ```

3. Set up environment variables for Azure DevOps:
   ```bash
   export AZURE_DEVOPS_TOKEN=your_personal_access_token
   export AZURE_DEVOPS_ORG=your_organization
   export AZURE_DEVOPS_PROJECT=your_project
   ```

4. Run the server:
   ```bash
   npm start
   ```

5. Configure an MCP client to use the server by adding it to the MCP configuration file

6. Potential future enhancements:
   - Add more Azure DevOps API features (e.g., pipeline artifacts, build logs)
   - Implement caching for pipeline lists
   - Add support for more complex pipeline variables
   - Create a Docker container for easier deployment