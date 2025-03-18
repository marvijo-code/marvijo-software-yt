/**
 * Integration tests for the Azure DevOps MCP Server
 * 
 * These tests simulate MCP tool calls and use Nock to intercept HTTP requests
 * to the Azure DevOps API.
 */

import { jest } from '@jest/globals';
import nock from 'nock';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { McpError } from '@modelcontextprotocol/sdk/types.js';

// Mock environment variables
process.env.AZURE_DEVOPS_TOKEN = 'mock-token';
process.env.AZURE_DEVOPS_ORG = 'mock-org';
process.env.AZURE_DEVOPS_PROJECT = 'mock-project';

// Mock the StdioServerTransport
jest.mock('@modelcontextprotocol/sdk/server/stdio.js', () => ({
  StdioServerTransport: jest.fn().mockImplementation(() => ({
    onmessage: null,
    send: jest.fn(),
    close: jest.fn().mockResolvedValue(undefined),
  })),
}));

// Import the server after mocking environment variables
// Note: In a real test, we would import the actual server
// For this test, we'll create a simplified version
class AzureDevOpsMcpServer {
  constructor() {
    this.server = new Server({
      name: 'azure-devops-mcp-server',
      version: '0.1.0',
      capabilities: {
        tools: {
          list_pipelines: {
            description: 'List all pipelines in the Azure DevOps project',
            inputSchema: {
              type: 'object',
              properties: {},
              required: [],
            },
          },
          trigger_pipeline: {
            description: 'Trigger a pipeline run by name',
            inputSchema: {
              type: 'object',
              properties: {
                name: {
                  type: 'string',
                  description: 'Name of the pipeline to trigger',
                },
                variables: {
                  type: 'object',
                  description: 'Optional variables to pass to the pipeline',
                  additionalProperties: {
                    type: 'string',
                  },
                },
              },
              required: ['name'],
            },
          },
        },
      },
    });

    this.baseUrl = `https://dev.azure.com/${process.env.AZURE_DEVOPS_ORG}/${process.env.AZURE_DEVOPS_PROJECT}/_apis`;
    
    // Set up request handlers
    this.setupToolHandlers();
  }

  setupToolHandlers() {
    // Register tool handlers
    this.server.registerToolHandler('list_pipelines', async () => {
      
      try {
        const response = await fetch(`${this.baseUrl}/pipelines?api-version=7.0`, {
          headers: {
            'Authorization': `Basic ${Buffer.from(`:${process.env.AZURE_DEVOPS_TOKEN}`).toString('base64')}`,
          },
        });
        
        if (!response.ok) {
          throw new Error(`Failed to list pipelines: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(data.value, null, 2),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });

    this.server.setRequestHandler('call_tool', async (request) => {
      if (request.params.name !== 'trigger_pipeline') {
        return;
      }
      
      try {
        const { name, variables = {} } = request.params.arguments;
        
        // First, find the pipeline by name
        const listResponse = await fetch(`${this.baseUrl}/pipelines?api-version=7.0`, {
          headers: {
            'Authorization': `Basic ${Buffer.from(`:${process.env.AZURE_DEVOPS_TOKEN}`).toString('base64')}`,
          },
        });
        
        if (!listResponse.ok) {
          throw new Error(`Failed to list pipelines: ${listResponse.statusText}`);
        }
        
        const listData = await listResponse.json();
        const pipeline = listData.value.find(p => p.name === name);
        
        if (!pipeline) {
          throw new McpError('invalid_params', `Pipeline not found: ${name}`);
        }
        
        // Then, trigger the pipeline
        const payload = {
          variables: Object.entries(variables).reduce((acc, [key, value]) => {
            acc[key] = { value };
            return acc;
          }, {})
        };
        
        const triggerResponse = await fetch(`${this.baseUrl}/pipelines/${pipeline.id}/runs?api-version=7.0`, {
          method: 'POST',
          headers: {
            'Authorization': `Basic ${Buffer.from(`:${process.env.AZURE_DEVOPS_TOKEN}`).toString('base64')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });
        
        if (!triggerResponse.ok) {
          throw new Error(`Failed to trigger pipeline: ${triggerResponse.statusText}`);
        }
        
        const triggerData = await triggerResponse.json();
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(triggerData, null, 2),
            },
          ],
        };
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async run() {
    // In a real implementation, this would connect to a transport
    console.log('Azure DevOps MCP server running');
  }
}

describe('Azure DevOps MCP Server Integration Tests', () => {
  let server;
  
  beforeEach(() => {
    // Create a new server instance for each test
    server = new AzureDevOpsMcpServer();
    
    // Enable Nock for intercepting HTTP requests
    nock.disableNetConnect();
  });
  
  afterEach(() => {
    // Clean up Nock
    nock.cleanAll();
    nock.enableNetConnect();
  });
  
  describe('list_pipelines tool', () => {
    it('should return a list of pipelines', async () => {
      // Mock the Azure DevOps API response
      const mockPipelines = [
        { id: 1, name: 'Pipeline 1' },
        { id: 2, name: 'Pipeline 2' }
      ];
      
      nock('https://dev.azure.com')
        .get(`/mock-org/mock-project/_apis/pipelines`)
        .query({ 'api-version': '7.0' })
        .reply(200, { value: mockPipelines });
      
      // Simulate an MCP tool call
      const response = await server.server.handleRequest({
        method: 'call_tool',
        params: {
          name: 'list_pipelines',
          arguments: {},
        },
      });
      
      // Verify the response
      expect(response).toEqual({
        content: [
          {
            type: 'text',
            text: JSON.stringify(mockPipelines, null, 2),
          },
        ],
      });
    });
    
    it('should handle API errors', async () => {
      // Mock an API error
      nock('https://dev.azure.com')
        .get(`/mock-org/mock-project/_apis/pipelines`)
        .query({ 'api-version': '7.0' })
        .reply(500, { message: 'Internal server error' });
      
      // Simulate an MCP tool call
      const response = await server.server.handleRequest({
        method: 'call_tool',
        params: {
          name: 'list_pipelines',
          arguments: {},
        },
      });
      
      // Verify the response contains an error
      expect(response.isError).toBe(true);
      expect(response.content[0].text).toContain('Error:');
    });
  });
  
  describe('trigger_pipeline tool', () => {
    it('should trigger a pipeline run', async () => {
      const pipelineName = 'Pipeline 1';
      const pipelineId = 1;
      const mockVariables = { var1: 'value1' };
      
      // Mock the pipeline list API response
      const mockPipelines = [
        { id: pipelineId, name: pipelineName },
        { id: 2, name: 'Pipeline 2' }
      ];
      
      nock('https://dev.azure.com')
        .get(`/mock-org/mock-project/_apis/pipelines`)
        .query({ 'api-version': '7.0' })
        .reply(200, { value: mockPipelines });
      
      // Mock the pipeline trigger API response
      const mockRunResponse = { id: 123, status: 'queued' };
      
      nock('https://dev.azure.com')
        .post(`/mock-org/mock-project/_apis/pipelines/${pipelineId}/runs`, {
          variables: {
            var1: { value: 'value1' }
          }
        })
        .query({ 'api-version': '7.0' })
        .reply(200, mockRunResponse);
      
      // Simulate an MCP tool call
      const response = await server.server.handleRequest({
        method: 'call_tool',
        params: {
          name: 'trigger_pipeline',
          arguments: {
            name: pipelineName,
            variables: mockVariables,
          },
        },
      });
      
      // Verify the response
      expect(response).toEqual({
        content: [
          {
            type: 'text',
            text: JSON.stringify(mockRunResponse, null, 2),
          },
        ],
      });
    });
    
    it('should handle pipeline not found', async () => {
      const pipelineName = 'Non-existent Pipeline';
      
      // Mock the pipeline list API response with no matching pipeline
      const mockPipelines = [
        { id: 1, name: 'Pipeline 1' },
        { id: 2, name: 'Pipeline 2' }
      ];
      
      nock('https://dev.azure.com')
        .get(`/mock-org/mock-project/_apis/pipelines`)
        .query({ 'api-version': '7.0' })
        .reply(200, { value: mockPipelines });
      
      // Expect the request to throw an MCP error
      await expect(server.server.handleRequest({
        method: 'call_tool',
        params: {
          name: 'trigger_pipeline',
          arguments: {
            name: pipelineName,
          },
        },
      })).rejects.toThrow(`Pipeline not found: ${pipelineName}`);
    });
    
    it('should handle API errors when triggering a pipeline', async () => {
      const pipelineName = 'Pipeline 1';
      const pipelineId = 1;
      
      // Mock the pipeline list API response
      const mockPipelines = [
        { id: pipelineId, name: pipelineName },
        { id: 2, name: 'Pipeline 2' }
      ];
      
      nock('https://dev.azure.com')
        .get(`/mock-org/mock-project/_apis/pipelines`)
        .query({ 'api-version': '7.0' })
        .reply(200, { value: mockPipelines });
      
      // Mock an API error when triggering the pipeline
      nock('https://dev.azure.com')
        .post(`/mock-org/mock-project/_apis/pipelines/${pipelineId}/runs`)
        .query({ 'api-version': '7.0' })
        .reply(500, { message: 'Internal server error' });
      
      // Simulate an MCP tool call
      const response = await server.server.handleRequest({
        method: 'call_tool',
        params: {
          name: 'trigger_pipeline',
          arguments: {
            name: pipelineName,
          },
        },
      });
      
      // Verify the response contains an error
      expect(response.isError).toBe(true);
      expect(response.content[0].text).toContain('Error:');
    });
  });
});