const express = require('express');
const { config, validateConfig } = require('./config');
const pipelineRoutes = require('./routes/pipelineRoutes');
const errorHandler = require('./middleware/errorHandler');

// Validate configuration
try {
  validateConfig();
} catch (error) {
  console.error('Configuration error:', error.message);
  process.exit(1);
}

// Initialize Express app
const app = express();
const PORT = config.server.port;

// Middleware
app.use(express.json());

// Routes
app.use('/pipelines', pipelineRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Error handling middleware
app.use(errorHandler);

// Start server only if this file is run directly (not required/imported)
if (require.main === module) {
  const server = app.listen(PORT, () => {
    console.log(`MCP Server running on port ${PORT}`);
    console.log(`Connected to Azure DevOps organization: ${config.azure.organization}`);
    console.log(`Connected to Azure DevOps project: ${config.azure.project}`);
  });
}

module.exports = app; 