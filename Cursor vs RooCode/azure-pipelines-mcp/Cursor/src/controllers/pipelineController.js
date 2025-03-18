const azureDevOpsClient = require('../utils/azureDevOpsClient');

/**
 * Get all pipelines
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
const getPipelines = async (req, res, next) => {
  try {
    const pipelines = await azureDevOpsClient.getPipelines();
    
    const formattedPipelines = pipelines.map(pipeline => ({
      id: pipeline.id,
      name: pipeline.name,
      url: pipeline._links?.web?.href || '',
    }));
    
    res.json({ pipelines: formattedPipelines });
  } catch (error) {
    next(error);
  }
};

/**
 * Run a pipeline by name
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
const runPipeline = async (req, res, next) => {
  try {
    const { pipelineName } = req.body;
    
    if (!pipelineName) {
      return res.status(400).json({ error: 'Pipeline name is required' });
    }
    
    const result = await azureDevOpsClient.runPipeline(pipelineName);
    res.json(result);
  } catch (error) {
    if (error.message.includes('not found')) {
      return res.status(404).json({ error: error.message });
    }
    next(error);
  }
};

module.exports = {
  getPipelines,
  runPipeline,
}; 