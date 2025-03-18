/**
 * Unit tests for the AzureDevOpsClient class
 */

import { jest } from '@jest/globals';
import * as axiosModule from 'axios';

// Create a mock for axios
const axios = {
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn()
  }))
};

// Mock axios
jest.mock('axios', () => {
  return {
    __esModule: true,
    ...axios
  };
});

// Import the AzureDevOpsClient class
// Note: We need to extract the class from index.js for testing
// This is a simplified version for testing purposes
class AzureDevOpsClient {
  constructor(token, organization, project) {
    this.token = token;
    this.organization = organization;
    this.project = project;
    this.baseUrl = `https://dev.azure.com/${organization}/${project}/_apis`;
    
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

  async listPipelines() {
    try {
      const response = await this.axiosInstance.get('/pipelines?api-version=7.0');
      return response.data.value;
    } catch (error) {
      throw new Error(`Failed to list pipelines: ${error.message}`);
    }
  }

  async findPipelineByName(name) {
    try {
      const pipelines = await this.listPipelines();
      return pipelines.find(pipeline => pipeline.name === name) || null;
    } catch (error) {
      throw new Error(`Failed to find pipeline by name: ${error.message}`);
    }
  }

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
      throw new Error(`Failed to trigger pipeline: ${error.message}`);
    }
  }
}

describe('AzureDevOpsClient', () => {
  const mockToken = 'mock-token';
  const mockOrg = 'mock-org';
  const mockProject = 'mock-project';
  let client;

  beforeEach(() => {
    client = new AzureDevOpsClient(mockToken, mockOrg, mockProject);
    
    // Reset mocks
    jest.clearAllMocks();
  });

  describe('constructor', () => {
    it('should create an instance with the correct properties', () => {
      expect(client.token).toBe(mockToken);
      expect(client.organization).toBe(mockOrg);
      expect(client.project).toBe(mockProject);
      expect(client.baseUrl).toBe(`https://dev.azure.com/${mockOrg}/${mockProject}/_apis`);
    });

    it('should create an axios instance with the correct configuration', () => {
      expect(axios.create).toHaveBeenCalledWith({
        baseURL: client.baseUrl,
        headers: {
          'Content-Type': 'application/json',
        },
        auth: {
          username: '',
          password: mockToken
        }
      });
    });
  });

  describe('listPipelines', () => {
    it('should return pipelines when the API call is successful', async () => {
      const mockPipelines = [
        { id: 1, name: 'Pipeline 1' },
        { id: 2, name: 'Pipeline 2' }
      ];
      
      const mockResponse = {
        data: {
          value: mockPipelines
        }
      };
      
      client.axiosInstance.get.mockResolvedValueOnce(mockResponse);
      
      const result = await client.listPipelines();
      
      expect(client.axiosInstance.get).toHaveBeenCalledWith('/pipelines?api-version=7.0');
      expect(result).toEqual(mockPipelines);
    });

    it('should throw an error when the API call fails', async () => {
      const errorMessage = 'API error';
      client.axiosInstance.get.mockRejectedValueOnce(new Error(errorMessage));
      
      await expect(client.listPipelines()).rejects.toThrow(`Failed to list pipelines: ${errorMessage}`);
    });
  });

  describe('findPipelineByName', () => {
    it('should return the pipeline when it exists', async () => {
      const mockPipelines = [
        { id: 1, name: 'Pipeline 1' },
        { id: 2, name: 'Pipeline 2' }
      ];
      
      // Mock the listPipelines method
      client.listPipelines = jest.fn().mockResolvedValueOnce(mockPipelines);
      
      const result = await client.findPipelineByName('Pipeline 2');
      
      expect(client.listPipelines).toHaveBeenCalled();
      expect(result).toEqual(mockPipelines[1]);
    });

    it('should return null when the pipeline does not exist', async () => {
      const mockPipelines = [
        { id: 1, name: 'Pipeline 1' },
        { id: 2, name: 'Pipeline 2' }
      ];
      
      // Mock the listPipelines method
      client.listPipelines = jest.fn().mockResolvedValueOnce(mockPipelines);
      
      const result = await client.findPipelineByName('Pipeline 3');
      
      expect(client.listPipelines).toHaveBeenCalled();
      expect(result).toBeNull();
    });

    it('should throw an error when listPipelines fails', async () => {
      const errorMessage = 'Failed to list pipelines';
      client.listPipelines = jest.fn().mockRejectedValueOnce(new Error(errorMessage));
      
      await expect(client.findPipelineByName('Pipeline 1')).rejects.toThrow(`Failed to find pipeline by name: ${errorMessage}`);
    });
  });

  describe('triggerPipeline', () => {
    it('should trigger a pipeline run without variables', async () => {
      const mockPipelineId = 1;
      const mockRunResponse = { id: 123, status: 'queued' };
      
      client.axiosInstance.post.mockResolvedValueOnce({ data: mockRunResponse });
      
      const result = await client.triggerPipeline(mockPipelineId);
      
      expect(client.axiosInstance.post).toHaveBeenCalledWith(
        `/pipelines/${mockPipelineId}/runs?api-version=7.0`,
        { variables: {} }
      );
      expect(result).toEqual(mockRunResponse);
    });

    it('should trigger a pipeline run with variables', async () => {
      const mockPipelineId = 1;
      const mockVariables = { var1: 'value1', var2: 'value2' };
      const mockRunResponse = { id: 123, status: 'queued' };
      
      client.axiosInstance.post.mockResolvedValueOnce({ data: mockRunResponse });
      
      const result = await client.triggerPipeline(mockPipelineId, mockVariables);
      
      expect(client.axiosInstance.post).toHaveBeenCalledWith(
        `/pipelines/${mockPipelineId}/runs?api-version=7.0`,
        {
          variables: {
            var1: { value: 'value1' },
            var2: { value: 'value2' }
          }
        }
      );
      expect(result).toEqual(mockRunResponse);
    });

    it('should throw an error when the API call fails', async () => {
      const mockPipelineId = 1;
      const errorMessage = 'API error';
      
      client.axiosInstance.post.mockRejectedValueOnce(new Error(errorMessage));
      
      await expect(client.triggerPipeline(mockPipelineId)).rejects.toThrow(`Failed to trigger pipeline: ${errorMessage}`);
    });
  });
});