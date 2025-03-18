const express = require('express');
const router = express.Router();
const pipelineController = require('../controllers/pipelineController');

/**
 * @route GET /pipelines
 * @desc Get all pipelines
 * @access Public
 */
router.get('/', pipelineController.getPipelines);

/**
 * @route POST /pipelines/run
 * @desc Run a pipeline by name
 * @access Public
 */
router.post('/run', pipelineController.runPipeline);

module.exports = router; 