const request = require('supertest');
const app = require('../../src/index');
const azureDevOpsClient = require('../../src/utils/azureDevOpsClient');

// Mock the Azure DevOps client
jest.mock('../../src/utils/azureDevOpsClient');

describe('Pipeline API Endpoints', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /pipelines', () => {
    test('should return list of pipelines', async () => {
      const mockPipelines = [
        { id: '1', name: 'Pipeline 1', _links: { web: { href: 'https://example.com/1' } } },
        { id: '2', name: 'Pipeline 2', _links: { web: { href: 'https://example.com/2' } } },
      ];

      azureDevOpsClient.getPipelines.mockResolvedValue(mockPipelines);

      const response = await request(app).get('/pipelines');

      expect(response.status).toBe(200);
      expect(response.body).toEqual({
        pipelines: [
          { id: '1', name: 'Pipeline 1', url: 'https://example.com/1' },
          { id: '2', name: 'Pipeline 2', url: 'https://example.com/2' },
        ],
      });
      expect(azureDevOpsClient.getPipelines).toHaveBeenCalled();
    });

    test('should return 500 when API call fails', async () => {
      azureDevOpsClient.getPipelines.mockRejectedValue(new Error('API error'));

      const response = await request(app).get('/pipelines');

      expect(response.status).toBe(500);
      expect(response.body).toHaveProperty('error');
      expect(azureDevOpsClient.getPipelines).toHaveBeenCalled();
    });
  });

  describe('POST /pipelines/run', () => {
    test('should return 400 when pipelineName is missing', async () => {
      const response = await request(app)
        .post('/pipelines/run')
        .send({});

      expect(response.status).toBe(400);
      expect(response.body).toEqual({ error: 'Pipeline name is required' });
      expect(azureDevOpsClient.runPipeline).not.toHaveBeenCalled();
    });

    test('should return pipeline run details when successful', async () => {
      const mockRunResult = {
        id: '123',
        name: 'Pipeline 1',
        status: 'queued',
        url: 'https://example.com/run/123',
      };

      azureDevOpsClient.runPipeline.mockResolvedValue(mockRunResult);

      const response = await request(app)
        .post('/pipelines/run')
        .send({ pipelineName: 'Pipeline 1' });

      expect(response.status).toBe(200);
      expect(response.body).toEqual(mockRunResult);
      expect(azureDevOpsClient.runPipeline).toHaveBeenCalledWith('Pipeline 1');
    });

    test('should return 404 when pipeline not found', async () => {
      const error = new Error("Pipeline with name 'Non-existent Pipeline' not found");
      azureDevOpsClient.runPipeline.mockRejectedValue(error);

      const response = await request(app)
        .post('/pipelines/run')
        .send({ pipelineName: 'Non-existent Pipeline' });

      expect(response.status).toBe(404);
      expect(response.body).toEqual({ error: error.message });
      expect(azureDevOpsClient.runPipeline).toHaveBeenCalledWith('Non-existent Pipeline');
    });

    test('should return 500 for other errors', async () => {
      azureDevOpsClient.runPipeline.mockRejectedValue(new Error('Internal server error'));

      const response = await request(app)
        .post('/pipelines/run')
        .send({ pipelineName: 'Pipeline 1' });

      expect(response.status).toBe(500);
      expect(response.body).toHaveProperty('error');
      expect(azureDevOpsClient.runPipeline).toHaveBeenCalledWith('Pipeline 1');
    });
  });

  describe('GET /health', () => {
    test('should return health status', async () => {
      const response = await request(app).get('/health');

      expect(response.status).toBe(200);
      expect(response.body).toEqual({ status: 'ok' });
    });
  });
}); 