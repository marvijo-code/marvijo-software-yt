/**
 * Jest configuration for the Azure DevOps MCP Server
 */

export default {
  // Use the Node.js environment
  testEnvironment: 'node',
  
  // Transform ES modules
  transform: {},
  
  // Set moduleNameMapper for ES modules
  moduleNameMapper: {
    '^axios$': '<rootDir>/node_modules/axios/dist/axios.js'
  },
  
  // Specify test match patterns
  testMatch: [
    '**/test/unit/**/*.test.js',
    '**/test/integration/**/*.test.js'
  ],
  
  // Specify test coverage collection
  collectCoverage: true,
  collectCoverageFrom: [
    'index.js',
    '!**/node_modules/**',
    '!**/test/**'
  ],
  coverageDirectory: 'coverage',
  
  // Specify test reporters
  reporters: ['default'],
  
  // Specify test timeout
  testTimeout: 10000,
  
  // Specify test setup files
  setupFilesAfterEnv: [],
  
  // Specify test environment variables
  testEnvironmentOptions: {
    // Add any environment variables needed for tests
  },
  
  // Verbose output
  verbose: true
};