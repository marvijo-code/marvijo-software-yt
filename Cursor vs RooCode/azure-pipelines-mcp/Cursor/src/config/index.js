require('dotenv').config();

const config = {
  azure: {
    token: process.env.AZURE_DEVOPS_TOKEN,
    organization: process.env.AZURE_DEVOPS_ORGANIZATION,
    project: process.env.AZURE_DEVOPS_PROJECT,
  },
  server: {
    port: process.env.PORT || 3000,
  },
};

// Validate required configuration
const validateConfig = () => {
  const requiredVars = [
    { key: 'azure.token', value: config.azure.token },
    { key: 'azure.organization', value: config.azure.organization },
    { key: 'azure.project', value: config.azure.project },
  ];

  const missingVars = requiredVars.filter(({ value }) => !value);

  if (missingVars.length > 0) {
    const missingKeys = missingVars.map(({ key }) => key).join(', ');
    throw new Error(`Missing required environment variables: ${missingKeys}`);
  }
};

module.exports = {
  config,
  validateConfig,
}; 