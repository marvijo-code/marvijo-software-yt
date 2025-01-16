# New Knowledge Base

- Crawl4AI can be run locally using Docker instead of using their API service, which provides more control and eliminates the need for API keys
- Crawl4AI supports Bearer token authentication when running locally, configured through CRAWL4AI_API_TOKEN environment variable
- Material-UI Drawer focus management requires careful configuration (disableAutoFocus, disableEnforceFocus, keepMounted) to prevent focus stealing in mobile interfaces
- Vite configuration should use process.env to access environment variables, not vite.env
- The project uses a dual-port setup with frontend on 5503 and API on 5501
- When using Node.js v22+ with "type": "module", plugins need to be imported dynamically using await import()
- Radix UI Dialog (Sheet) components need explicit cleanup of body styles on close to prevent lingering effects
- Component props should be consistently named throughout the component to prevent undefined references
