jest.mock('axios');
jest.mock('../../src/config', () => ({
  config: {
    azure: {
      token: 'test-token',
      organization: 'test-org',
      project: 'test-project',
    },
  },
}));

describe('Azure DevOps Client', () => {
  let azureDevOpsClient;
  let mockAxios;
  
  beforeEach(() => {
    jest.resetModules();
    
    // Create a mock axios instance
    mockAxios = {
      get: jest.fn(),
      post: jest.fn(),
    };
    
    // Mock axios.create to return our mock instance
    const axios = require('axios');
    axios.create = jest.fn().mockReturnValue(mockAxios);
    
    // Now require the client
    azureDevOpsClient = require('../../src/utils/azureDevOpsClient');
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  describe('getPipelines', () => {
    test('should return pipelines when API call is successful', async () => {
      const mockPipelines = [
        { id: '1', name: 'Pipeline 1', _links: { web: { href: 'https://example.com/1' } } },
        { id: '2', name: 'Pipeline 2', _links: { web: { href: 'https://example.com/2' } } },
      ];
      
      mockAxios.get.mockResolvedValueOnce({
        data: { value: mockPipelines },
      });
      
      const result = await azureDevOpsClient.getPipelines();
      
      expect(mockAxios.get).toHaveBeenCalledWith('/_apis/pipelines?api-version=7.1-preview.1');
      expect(result).toEqual(mockPipelines);
    });
    
    test('should throw error when API call fails', async () => {
      mockAxios.get.mockRejectedValueOnce(new Error('API error'));
      
      await expect(azureDevOpsClient.getPipelines()).rejects.toThrow('Failed to fetch pipelines');
    });
  });
  
  describe('getPipelineByName', () => {
    test('should return pipeline when found by name', async () => {
      const mockPipelines = [
        { id: '1', name: 'Pipeline 1', _links: { web: { href: 'https://example.com/1' } } },
        { id: '2', name: 'Pipeline 2', _links: { web: { href: 'https://example.com/2' } } },
      ];
      
      mockAxios.get.mockResolvedValueOnce({
        data: { value: mockPipelines },
      });
      
      const result = await azureDevOpsClient.getPipelineByName('Pipeline 1');
      
      expect(mockAxios.get).toHaveBeenCalledWith('/_apis/pipelines?api-version=7.1-preview.1');
      expect(result).toEqual(mockPipelines[0]);
    });
    
    test('should throw error when pipeline not found by name', async () => {
      const mockPipelines = [
        { id: '1', name: 'Pipeline 1', _links: { web: { href: 'https://example.com/1' } } },
      ];
      
      mockAxios.get.mockResolvedValueOnce({
        data: { value: mockPipelines },
      });
      
      await expect(azureDevOpsClient.getPipelineByName('Non-existent Pipeline')).rejects.toThrow(
        "Pipeline with name 'Non-existent Pipeline' not found"
      );
    });
  });
  
  describe('runPipeline', () => {
    test('should run pipeline and return details when successful', async () => {
      const mockPipeline = { id: '1', name: 'Pipeline 1', _links: { web: { href: 'https://example.com/1' } } };
      const mockRunResponse = {
        data: {
          id: '123',
          state: 'queued',
          _links: { web: { href: 'https://example.com/run/123' } },
        },
      };
      
      // Mock getPipelineByName by mocking the get request for pipelines
      mockAxios.get.mockResolvedValueOnce({
        data: { value: [mockPipeline] },
      });
      
      // Mock post request
      mockAxios.post.mockResolvedValueOnce(mockRunResponse);
      
      const result = await azureDevOpsClient.runPipeline('Pipeline 1');
      
      expect(mockAxios.get).toHaveBeenCalledWith('/_apis/pipelines?api-version=7.1-preview.1');
      expect(mockAxios.post).toHaveBeenCalledWith(
        '/_apis/pipelines/1/runs?api-version=7.1-preview.1',
        expect.any(Object)
      );
      
      expect(result).toEqual({
        id: '123',
        name: 'Pipeline 1',
        status: 'queued',
        url: 'https://example.com/run/123',
      });
    });
    
    test('should throw error when pipeline run fails', async () => {
      const mockPipeline = { id: '1', name: 'Pipeline 1', _links: { web: { href: 'https://example.com/1' } } };
      
      // Mock getPipelineByName
      mockAxios.get.mockResolvedValueOnce({
        data: { value: [mockPipeline] },
      });
      
      // Mock post request failure
      mockAxios.post.mockRejectedValueOnce(new Error('Run failed'));
      
      await expect(azureDevOpsClient.runPipeline('Pipeline 1')).rejects.toThrow('Run failed');
    });
  });
});