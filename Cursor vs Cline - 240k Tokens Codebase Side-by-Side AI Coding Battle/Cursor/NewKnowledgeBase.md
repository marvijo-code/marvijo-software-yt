# New Knowledge Base

- Vite configuration should use process.env to access environment variables, not vite.env
- The project uses a dual-port setup with frontend on 5503 and API on 5501
- When using Node.js v22+ with "type": "module", plugins need to be imported dynamically using await import()
- Radix UI Dialog (Sheet) components need explicit cleanup of body styles on close to prevent lingering effects
- Component props should be consistently named throughout the component to prevent undefined references 
- Search filtering can be optimized by moving it from individual match components to the group level for better performance and UX 
- The application now integrates with Serper for Google search and Microsoft.Playwright for web scraping to provide match-related news
- Microsoft.Playwright in .NET requires manual cleanup of browser and playwright instances through IAsyncDisposable 