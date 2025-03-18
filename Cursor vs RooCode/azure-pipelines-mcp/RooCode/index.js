#!/usr/bin/env node

/**
 * Azure DevOps MCP Server
 * 
 * This server provides MCP tools for interacting with Azure DevOps pipelines:
 * - list_pipelines: Lists all pipelines in a project
 * - trigger_pipeline: Triggers a pipeline run by name
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

// Load dot env
import dotenv from 'dotenv';
dotenv.config();

// Environment variables
const API_TOKEN = process.env.AZURE_DEVOPS_TOKEN;
const ORGANIZATION = process.env.AZURE_DEVOPS_ORG;
const PROJECT = process.env.AZURE_DEVOPS_PROJECT;

// Validate required environment variables
if (!API_TOKEN) {
  console.error('Error: AZURE_DEVOPS_TOKEN environment variable is required');
  process.exit(1);
}

if (!ORGANIZATION) {
  console.error('Error: AZURE_DEVOPS_ORG environment variable is required');
  process.exit(1);
}

if (!PROJECT) {
  console.error('Error: AZURE_DEVOPS_PROJECT environment variable is required');
  process.exit(1);
}

/**
 * Azure DevOps API Client
 * Handles communication with the Azure DevOps REST API
 */
class AzureDevOpsClient {
  constructor(token, organization, project) {
    this.token = token;
    this.organization = organization;
    this.project = project;
    this.baseUrl = `https://dev.azure.com/${organization}/${project}/_apis`;
    
    // Create axios instance with authentication
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
      auth: {
        username: '',
        password: token
      }
    });
  }

  /**
   * List all pipelines in the project
   * @returns {Promise<Array>} Array of pipeline objects
   */
  async listPipelines() {
    try {
      const response = await this.axiosInstance.get('/pipelines?api-version=7.0');
      return response.data.value;
    } catch (error) {
      console.error('Error listing pipelines:', error.message);
      if (error.response) {
        console.error('Response data:', error.response.data);
      }
      throw new Error(`Failed to list pipelines: ${error.message}`);
    }
  }

  /**
   * Find a pipeline by name
   * @param {string} name - The name of the pipeline to find
   * @returns {Promise<Object|null>} The pipeline object or null if not found
   */
  async findPipelineByName(name) {
    try {
      const pipelines = await this.listPipelines();
      return pipelines.find(pipeline => pipeline.name === name) || null;
    } catch (error) {
      console.error('Error finding pipeline by name:', error.message);
      throw new Error(`Failed to find pipeline by name: ${error.message}`);
    }
  }

  /**
   * Trigger a pipeline run
   * @param {number} pipelineId - The ID of the pipeline to trigger
   * @param {Object} variables - Optional variables to pass to the pipeline
   * @returns {Promise<Object>} The pipeline run object
   */
  async triggerPipeline(pipelineId, variables = {}) {
    try {
      const payload = {
        variables: Object.entries(variables).reduce((acc, [key, value]) => {
          acc[key] = { value };
          return acc;
        }, {})
      };

      const response = await this.axiosInstance.post(
        `/pipelines/${pipelineId}/runs?api-version=7.0`,
        payload
      );
      
      return response.data;
    } catch (error) {
      console.error('Error triggering pipeline:', error.message);
      if (error.response) {
        console.error('Response data:', error.response.data);
      }
      throw new Error(`Failed to trigger pipeline: ${error.message}`);
    }
  }
}

/**
 * Azure DevOps MCP Server
 * Provides MCP tools for interacting with Azure DevOps pipelines
 */
class AzureDevOpsMcpServer {
  constructor() {
    this.server = new Server(
      {
        name: 'azure-devops-mcp-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.azureDevOpsClient = new AzureDevOpsClient(API_TOKEN, ORGANIZATION, PROJECT);
    
    // Set up request handlers
    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  /**
   * Set up MCP tool handlers
   */
  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'list_pipelines',
          description: 'List all pipelines in the Azure DevOps project',
          inputSchema: {
            type: 'object',
            properties: {},
            required: [],
          },
        },
        {
          name: 'trigger_pipeline',
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
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'list_pipelines':
            return await this.handleListPipelines();
          case 'trigger_pipeline':
            return await this.handleTriggerPipeline(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        console.error(`Error handling tool ${name}:`, error);
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

  /**
   * Handle the list_pipelines tool
   * @returns {Promise<Object>} MCP response
   */
  async handleListPipelines() {
    try {
      const pipelines = await this.azureDevOpsClient.listPipelines();
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(pipelines, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to list pipelines: ${error.message}`);
    }
  }

  /**
   * Handle the trigger_pipeline tool
   * @param {Object} args - Tool arguments
   * @param {string} args.name - Name of the pipeline to trigger
   * @param {Object} args.variables - Optional variables to pass to the pipeline
   * @returns {Promise<Object>} MCP response
   */
  async handleTriggerPipeline(args) {
    if (!args.name) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Pipeline name is required'
      );
    }

    try {
      const pipeline = await this.azureDevOpsClient.findPipelineByName(args.name);
      
      if (!pipeline) {
        throw new McpError(
          ErrorCode.InvalidParams,
          `Pipeline not found: ${args.name}`
        );
      }

      const variables = args.variables || {};
      const run = await this.azureDevOpsClient.triggerPipeline(pipeline.id, variables);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(run, null, 2),
          },
        ],
      };
    } catch (error) {
      if (error instanceof McpError) {
        throw error;
      }
      throw new Error(`Failed to trigger pipeline: ${error.message}`);
    }
  }

  /**
   * Run the MCP server
   */
  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Azure DevOps MCP server running on stdio');
  }
}

// Create and run the server
const server = new AzureDevOpsMcpServer();
server.run().catch(console.error);