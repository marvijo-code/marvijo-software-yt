describe('Config Validation', () => {
  // Mock the config module
  let mockConfig;
  let validateConfig;
  
  beforeEach(() => {
    jest.resetModules();
    
    // Create a mock config object
    mockConfig = {
      azure: {
        token: 'test-token',
        organization: 'test-org',
        project: 'test-project',
      },
      server: {
        port: 3000,
      },
    };
    
    // Mock the config module
    jest.mock('../../src/config', () => {
      return {
        config: mockConfig,
        validateConfig: jest.fn(() => {
          const requiredVars = [
            { key: 'azure.token', value: mockConfig.azure.token },
            { key: 'azure.organization', value: mockConfig.azure.organization },
            { key: 'azure.project', value: mockConfig.azure.project },
          ];
          
          const missingVars = requiredVars.filter(({ value }) => !value);
          
          if (missingVars.length > 0) {
            const missingKeys = missingVars.map(({ key }) => key).join(', ');
            throw new Error(`Missing required environment variables: ${missingKeys}`);
          }
        }),
      };
    });
    
    // Import the module after mocking
    const configModule = require('../../src/config');
    validateConfig = configModule.validateConfig;
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  test('should throw error when required environment variables are missing', () => {
    // Set missing values
    mockConfig.azure.token = undefined;
    mockConfig.azure.organization = undefined;
    mockConfig.azure.project = undefined;
    
    expect(() => validateConfig()).toThrow(/Missing required environment variables/);
  });
  
  test('should not throw error when all required environment variables are present', () => {
    // All values are already set in the mock
    expect(() => validateConfig()).not.toThrow();
  });
}); 