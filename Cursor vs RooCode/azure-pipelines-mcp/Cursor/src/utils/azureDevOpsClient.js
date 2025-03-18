const axios = require('axios');
const { config } = require('../config');

class AzureDevOpsClient {
  constructor() {
    this.baseUrl = `https://dev.azure.com/${config.azure.organization}/${config.azure.project}`;
    this.token = config.azure.token;
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Authorization': `Basic ${Buffer.from(`:${this.token}`).toString('base64')}`,
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Get all pipelines in the project
   * @returns {Promise<Array>} List of pipelines
   */
  async getPipelines() {
    try {
      const response = await this.client.get('/_apis/pipelines?api-version=7.1-preview.1');
      return response.data.value;
    } catch (error) {
      console.error('Error fetching pipelines:', error.message);
      throw new Error(`Failed to fetch pipelines: ${error.message}`);
    }
  }

  /**
   * Get a pipeline by name
   * @param {string} name - Pipeline name
   * @returns {Promise<Object>} Pipeline details
   */
  async getPipelineByName(name) {
    try {
      const pipelines = await this.getPipelines();
      const pipeline = pipelines.find(p => p.name === name);
      
      if (!pipeline) {
        throw new Error(`Pipeline with name '${name}' not found`);
      }
      
      return pipeline;
    } catch (error) {
      console.error(`Error finding pipeline '${name}':`, error.message);
      throw error;
    }
  }

  /**
   * Run a pipeline by name
   * @param {string} name - Pipeline name
   * @returns {Promise<Object>} Pipeline run details
   */
  async runPipeline(name) {
    try {
      const pipeline = await this.getPipelineByName(name);
      
      const response = await this.client.post(
        `/_apis/pipelines/${pipeline.id}/runs?api-version=7.1-preview.1`,
        { resources: { repositories: { self: { refName: 'refs/heads/main' } } } }
      );
      
      return {
        id: response.data.id,
        name: pipeline.name,
        status: response.data.state,
        url: response.data._links.web.href,
      };
    } catch (error) {
      console.error(`Error running pipeline '${name}':`, error.message);
      throw error;
    }
  }
}

module.exports = new AzureDevOpsClient(); 