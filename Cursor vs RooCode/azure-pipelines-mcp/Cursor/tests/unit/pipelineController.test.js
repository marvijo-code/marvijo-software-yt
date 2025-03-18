const pipelineController = require('../../src/controllers/pipelineController');
const azureDevOpsClient = require('../../src/utils/azureDevOpsClient');

// Mock the Azure DevOps client
jest.mock('../../src/utils/azureDevOpsClient');

describe('Pipeline Controller', () => {
  let req, res, next;

  beforeEach(() => {
    req = {
      body: {},
    };
    res = {
      json: jest.fn(),
      status: jest.fn().mockReturnThis(),
    };
    next = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('getPipelines', () => {
    test('should return formatted pipelines when successful', async () => {
      const mockPipelines = [
        { id: '1', name: 'Pipeline 1', _links: { web: { href: 'https://example.com/1' } } },
        { id: '2', name: 'Pipeline 2', _links: { web: { href: 'https://example.com/2' } } },
      ];

      azureDevOpsClient.getPipelines.mockResolvedValue(mockPipelines);

      await pipelineController.getPipelines(req, res, next);

      expect(azureDevOpsClient.getPipelines).toHaveBeenCalled();
      expect(res.json).toHaveBeenCalledWith({
        pipelines: [
          { id: '1', name: 'Pipeline 1', url: 'https://example.com/1' },
          { id: '2', name: 'Pipeline 2', url: 'https://example.com/2' },
        ],
      });
      expect(next).not.toHaveBeenCalled();
    });

    test('should call next with error when getPipelines fails', async () => {
      const error = new Error('Failed to fetch pipelines');
      azureDevOpsClient.getPipelines.mockRejectedValue(error);

      await pipelineController.getPipelines(req, res, next);

      expect(azureDevOpsClient.getPipelines).toHaveBeenCalled();
      expect(res.json).not.toHaveBeenCalled();
      expect(next).toHaveBeenCalledWith(error);
    });
  });

  describe('runPipeline', () => {
    test('should return 400 when pipelineName is missing', async () => {
      await pipelineController.runPipeline(req, res, next);

      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith({ error: 'Pipeline name is required' });
      expect(azureDevOpsClient.runPipeline).not.toHaveBeenCalled();
      expect(next).not.toHaveBeenCalled();
    });

    test('should return pipeline run details when successful', async () => {
      req.body.pipelineName = 'Pipeline 1';
      
      const mockRunResult = {
        id: '123',
        name: 'Pipeline 1',
        status: 'queued',
        url: 'https://example.com/run/123',
      };

      azureDevOpsClient.runPipeline.mockResolvedValue(mockRunResult);

      await pipelineController.runPipeline(req, res, next);

      expect(azureDevOpsClient.runPipeline).toHaveBeenCalledWith('Pipeline 1');
      expect(res.json).toHaveBeenCalledWith(mockRunResult);
      expect(next).not.toHaveBeenCalled();
    });

    test('should return 404 when pipeline not found', async () => {
      req.body.pipelineName = 'Non-existent Pipeline';
      
      const error = new Error("Pipeline with name 'Non-existent Pipeline' not found");
      azureDevOpsClient.runPipeline.mockRejectedValue(error);

      await pipelineController.runPipeline(req, res, next);

      expect(azureDevOpsClient.runPipeline).toHaveBeenCalledWith('Non-existent Pipeline');
      expect(res.status).toHaveBeenCalledWith(404);
      expect(res.json).toHaveBeenCalledWith({ error: error.message });
      expect(next).not.toHaveBeenCalled();
    });

    test('should call next with error for other errors', async () => {
      req.body.pipelineName = 'Pipeline 1';
      
      const error = new Error('Internal server error');
      azureDevOpsClient.runPipeline.mockRejectedValue(error);

      await pipelineController.runPipeline(req, res, next);

      expect(azureDevOpsClient.runPipeline).toHaveBeenCalledWith('Pipeline 1');
      expect(res.json).not.toHaveBeenCalled();
      expect(next).toHaveBeenCalledWith(error);
    });
  });
}); 