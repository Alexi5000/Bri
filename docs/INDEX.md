# BRI Documentation Index

Welcome to the BRI documentation! This index helps you find the right documentation for your needs.

## 🚀 Getting Started

Start here if you're new to BRI:

1. **[README.md](../README.md)** - Project overview, features, and quick start
2. **[QUICKSTART.md](../QUICKSTART.md)** - Get up and running in 5 minutes
3. **[User Guide](USER_GUIDE.md)** - Complete guide to using BRI

## 📖 User Documentation

For users who want to use BRI to analyze videos:

- **[User Guide](USER_GUIDE.md)** - Complete usage instructions
  - Uploading videos
  - Asking questions
  - Understanding responses
  - Managing conversations
  - Tips & best practices

- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Solutions to common issues
  - Installation problems
  - Configuration errors
  - Processing issues
  - Performance optimization
  - Error message reference

- **[Configuration Reference](CONFIGURATION.md)** - All configuration options
  - Required settings
  - Optional settings
  - Environment-specific configs
  - Best practices

## 🔧 Developer Documentation

For developers who want to integrate with or contribute to BRI:

- **[MCP Server API](../mcp_server/README.md)** - REST API reference
  - Available tools
  - API endpoints
  - Request/response formats
  - Error handling

- **[API Examples](API_EXAMPLES.md)** - Practical API usage examples
  - curl examples
  - Python client examples
  - Batch processing
  - Error handling
  - Best practices

- **[Requirements](.kiro/specs/bri-video-agent/requirements.md)** - Feature requirements
  - User stories
  - Acceptance criteria
  - System requirements

- **[Design Document](.kiro/specs/bri-video-agent/design.md)** - System architecture
  - Architecture overview
  - Component design
  - Data models
  - Testing strategy

- **[Implementation Tasks](.kiro/specs/bri-video-agent/tasks.md)** - Development roadmap
  - Completed tasks
  - Pending tasks
  - Task dependencies

## 🚢 Deployment Documentation

For deploying BRI to production:

- **[Deployment Guide](../DEPLOYMENT.md)** - Production deployment
  - Docker deployment
  - Environment setup
  - Security considerations
  - Monitoring and logging

- **[Configuration Reference](CONFIGURATION.md)** - Production configuration
  - Environment variables
  - Security settings
  - Performance tuning

## 📚 Reference Documentation

### By Topic

#### Installation & Setup
- [README.md](../README.md) - Installation instructions
- [QUICKSTART.md](../QUICKSTART.md) - Quick setup guide
- [Configuration Reference](CONFIGURATION.md) - Configuration options
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Installation issues

#### Using BRI
- [User Guide](USER_GUIDE.md) - Complete usage guide
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Usage issues

#### API Integration
- [MCP Server API](../mcp_server/README.md) - API reference
- [API Examples](API_EXAMPLES.md) - Code examples

#### Development
- [Requirements](.kiro/specs/bri-video-agent/requirements.md) - What to build
- [Design Document](.kiro/specs/bri-video-agent/design.md) - How it's built
- [Implementation Tasks](.kiro/specs/bri-video-agent/tasks.md) - Development progress

#### Deployment
- [Deployment Guide](../DEPLOYMENT.md) - Production deployment
- [Configuration Reference](CONFIGURATION.md) - Production config

### By User Type

#### End Users
1. [README.md](../README.md) - Overview
2. [QUICKSTART.md](../QUICKSTART.md) - Get started
3. [User Guide](USER_GUIDE.md) - How to use
4. [Troubleshooting Guide](TROUBLESHOOTING.md) - Fix issues

#### Developers
1. [README.md](../README.md) - Overview
2. [Design Document](.kiro/specs/bri-video-agent/design.md) - Architecture
3. [MCP Server API](../mcp_server/README.md) - API reference
4. [API Examples](API_EXAMPLES.md) - Code examples
5. [Requirements](.kiro/specs/bri-video-agent/requirements.md) - Requirements

#### System Administrators
1. [Deployment Guide](../DEPLOYMENT.md) - Deploy to production
2. [Configuration Reference](CONFIGURATION.md) - Configure system
3. [Troubleshooting Guide](TROUBLESHOOTING.md) - Diagnose issues

## 🔍 Quick Links

### Common Tasks

- **Install BRI**: [README.md](../README.md#installation)
- **Configure API Key**: [Configuration Reference](CONFIGURATION.md#groq_api_key)
- **Upload a Video**: [User Guide](USER_GUIDE.md#uploading-videos)
- **Ask Questions**: [User Guide](USER_GUIDE.md#asking-questions)
- **Fix Errors**: [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Use the API**: [API Examples](API_EXAMPLES.md)
- **Deploy to Production**: [Deployment Guide](../DEPLOYMENT.md)

### Common Issues

- **Missing API Key**: [Troubleshooting Guide](TROUBLESHOOTING.md#missing-api-key)
- **Connection Refused**: [Troubleshooting Guide](TROUBLESHOOTING.md#connection-refused-errors)
- **Slow Processing**: [Troubleshooting Guide](TROUBLESHOOTING.md#processing-hangs-or-takes-too-long)
- **Out of Memory**: [Troubleshooting Guide](TROUBLESHOOTING.md#high-memory-usage)
- **Redis Errors**: [Troubleshooting Guide](TROUBLESHOOTING.md#redis-connection-fails)

## 📝 Documentation Standards

### For Contributors

When adding or updating documentation:

1. **Keep it user-focused**: Write for the reader's needs
2. **Use clear examples**: Show, don't just tell
3. **Update the index**: Add new docs to this index
4. **Cross-reference**: Link to related documentation
5. **Test instructions**: Verify all commands and examples work
6. **Use consistent formatting**: Follow existing style

### Documentation Structure

```
docs/
├── INDEX.md                    # This file
├── USER_GUIDE.md              # End-user documentation
├── TROUBLESHOOTING.md         # Problem-solving guide
├── CONFIGURATION.md           # Configuration reference
├── API_EXAMPLES.md            # API usage examples
└── [task-specific docs]       # Implementation documentation

Root level:
├── README.md                  # Project overview
├── QUICKSTART.md             # Quick start guide
├── DEPLOYMENT.md             # Deployment guide
└── mcp_server/README.md      # API reference
```

## 🆘 Getting Help

If you can't find what you're looking for:

1. **Search the docs**: Use your browser's search (Ctrl+F / Cmd+F)
2. **Check the index**: You're here! Look for related topics
3. **Try troubleshooting**: [Troubleshooting Guide](TROUBLESHOOTING.md)
4. **Ask the community**: GitHub Discussions
5. **Report issues**: GitHub Issues

## 📊 Documentation Coverage

### Completed Documentation

- ✅ Project overview and features
- ✅ Installation and setup
- ✅ User guide with examples
- ✅ Complete configuration reference
- ✅ Comprehensive troubleshooting guide
- ✅ API reference and examples
- ✅ Deployment guide
- ✅ Architecture and design docs
- ✅ Requirements and specifications

### Future Documentation

- ⏳ Video tutorials
- ⏳ Architecture diagrams (Mermaid)
- ⏳ Performance tuning guide
- ⏳ Security best practices
- ⏳ Migration guides
- ⏳ Contributing guidelines (detailed)
- ⏳ Code style guide

## 🔄 Documentation Updates

This documentation is actively maintained. Last updated: October 15, 2025

To suggest improvements:
- Open an issue on GitHub
- Submit a pull request
- Contact the maintainers

---

**Need help?** Start with the [User Guide](USER_GUIDE.md) or [Troubleshooting Guide](TROUBLESHOOTING.md)!

*Made with 💜 by the BRI community*
