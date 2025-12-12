# BRI Video Agent - Documentation Index

This guide helps you find the right documentation for your needs.

## 🚀 I Want To...

### Deploy the App for Testing
→ Start here: **[QUICK_START.md](QUICK_START.md)** (5 minutes)  
→ Full guide: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)** (comprehensive)

### Understand the System
→ Architecture: **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)**  
→ Overview: **[README.md](README.md)**  
→ Project structure: **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**

### Test the Application
→ Testing checklist: **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)**  
→ Deployment guide: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#testing-the-application)**

### Troubleshoot Issues
→ Quick fixes: **[QUICK_START.md](QUICK_START.md#troubleshooting)**  
→ Detailed guide: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#troubleshooting)**  
→ Check logs: `docker compose logs -f`

### Navigate Deployment Files
→ File guide: **[DEPLOYMENT_README.md](DEPLOYMENT_README.md)**  
→ What changed: **[DEPLOYMENT_CHANGES.md](DEPLOYMENT_CHANGES.md)**

---

## 📚 Documentation by Type

### Quick References (< 5 minutes)
- **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Overview of deployment
- **[DEPLOYMENT_README.md](DEPLOYMENT_README.md)** - Navigate deployment files

### Comprehensive Guides (15-30 minutes)
- **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)** - Complete deployment guide
- **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)** - Systematic testing
- **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)** - Architecture deep-dive
- **[README.md](README.md)** - Project overview and documentation

### Reference Documents
- **[DEPLOYMENT_CHANGES.md](DEPLOYMENT_CHANGES.md)** - What was changed
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **[.env.example](.env.example)** - Configuration reference
- **[docker-compose.yml](docker-compose.yml)** - Service configuration

---

## 👥 Documentation by User

### For End Users / Testers
1. **[QUICK_START.md](QUICK_START.md)** - How to deploy
2. **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)** - What to test
3. **[QUICK_START.md](QUICK_START.md#troubleshooting)** - Common issues

### For System Administrators / Operators
1. **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)** - Full deployment guide
2. **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)** - System architecture
3. **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Operational overview

### For Developers
1. **[README.md](README.md)** - Project overview
2. **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)** - Technical architecture
3. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Code organization
4. **[DEPLOYMENT_CHANGES.md](DEPLOYMENT_CHANGES.md)** - Recent changes

### For Project Managers / Stakeholders
1. **[README.md](README.md)** - Project overview and features
2. **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Deployment capabilities
3. **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)** - Acceptance criteria

---

## 🎯 Documentation by Task

### Task: First Time Deployment
1. Read: **[QUICK_START.md](QUICK_START.md)**
2. Run: `./preflight_check.sh`
3. Configure: Edit `.env`
4. Deploy: `./deploy_test.sh`
5. Test: Follow **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)**

### Task: Understanding the System
1. Read: **[README.md](README.md)** - Overview
2. Read: **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)** - Architecture
3. Review: `docker-compose.yml` - Configuration
4. Explore: `docker compose logs` - Runtime behavior

### Task: Systematic Testing
1. Follow: **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)**
2. Reference: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#testing-the-application)**
3. Monitor: `docker compose logs -f`
4. Check: `curl http://localhost:8000/health`

### Task: Troubleshooting
1. Check: **[QUICK_START.md](QUICK_START.md#troubleshooting)**
2. Review: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#troubleshooting)**
3. Run: `docker compose logs`
4. Verify: `docker compose ps`
5. Test: `curl http://localhost:8000/health`

### Task: Customization
1. Review: **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)**
2. Edit: `docker-compose.yml` - Services
3. Edit: `.env` - Configuration
4. Read: **[README.md](README.md#configuration)**
5. Rebuild: `docker compose build --no-cache`

---

## 📖 All Documentation Files

### Deployment Documentation
| File | Lines | Purpose | Read Time |
|------|-------|---------|-----------|
| [QUICK_START.md](QUICK_START.md) | 116 | Quick start guide | 5 min |
| [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md) | ~500 | Comprehensive deployment | 20 min |
| [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) | ~350 | Deployment overview | 10 min |
| [DEPLOYMENT_README.md](DEPLOYMENT_README.md) | ~300 | Navigation guide | 10 min |
| [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) | ~350 | System architecture | 20 min |
| [DEPLOYMENT_CHANGES.md](DEPLOYMENT_CHANGES.md) | ~400 | Change documentation | 15 min |

### Testing Documentation
| File | Lines | Purpose | Read Time |
|------|-------|---------|-----------|
| [TEST_CHECKLIST.md](TEST_CHECKLIST.md) | ~400 | Testing checklist | 30 min |

### Project Documentation
| File | Lines | Purpose | Read Time |
|------|-------|---------|-----------|
| [README.md](README.md) | ~445 | Project overview | 20 min |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | ~400 | Code structure | 15 min |
| [ARCHITECTURE_SUMMARY.md](ARCHITECTURE_SUMMARY.md) | ~180 | Architecture overview | 10 min |

### Reference Files
| File | Purpose |
|------|---------|
| [.env.example](.env.example) | Configuration template |
| [docker-compose.yml](docker-compose.yml) | Service orchestration |
| [Dockerfile.mcp](Dockerfile.mcp) | MCP Server image |
| [Dockerfile.ui](Dockerfile.ui) | Streamlit UI image |

---

## 🛠️ Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy_test.sh` | Deploy all services | `./deploy_test.sh` |
| `stop_test.sh` | Stop all services | `./stop_test.sh` |
| `preflight_check.sh` | Validate environment | `./preflight_check.sh` |

---

## 🗺️ Recommended Reading Paths

### Path 1: Quick Start (Total: 15 minutes)
1. **[QUICK_START.md](QUICK_START.md)** (5 min) - Deploy
2. Upload a video and test (10 min)

### Path 2: Full Understanding (Total: 60 minutes)
1. **[README.md](README.md)** (20 min) - Overview
2. **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)** (20 min) - Architecture
3. **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)** (20 min) - Deployment

### Path 3: Comprehensive (Total: 2 hours)
1. **[README.md](README.md)** (20 min)
2. **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)** (20 min)
3. **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)** (20 min)
4. **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)** (30 min)
5. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** (15 min)
6. **[DEPLOYMENT_CHANGES.md](DEPLOYMENT_CHANGES.md)** (15 min)

---

## 🔍 Find Specific Information

### Configuration
- Environment variables: **[.env.example](.env.example)**
- Service configuration: **[docker-compose.yml](docker-compose.yml)**
- Settings guide: **[README.md](README.md#configuration)**

### Architecture
- System overview: **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)**
- Component details: **[ARCHITECTURE_SUMMARY.md](ARCHITECTURE_SUMMARY.md)**
- Data flow: **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md#data-flow)**

### Deployment
- Quick deployment: **[QUICK_START.md](QUICK_START.md)**
- Full deployment: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)**
- Pre-flight checks: Run `./preflight_check.sh`

### Testing
- Test checklist: **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)**
- Test scenarios: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#testing-the-application)**

### Troubleshooting
- Quick fixes: **[QUICK_START.md](QUICK_START.md#troubleshooting)**
- Detailed troubleshooting: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#troubleshooting)**
- Common issues: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#common-issues)**

### Performance
- Expected metrics: **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md#performance-expectations)**
- Optimization: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#performance-tips)**
- Resource usage: Run `docker stats`

### Security
- Best practices: **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md#security)**
- Configuration: **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#configuration)**

---

## 💡 Tips

### For Quick Results
Start with **[QUICK_START.md](QUICK_START.md)** and run `./deploy_test.sh`

### For Comprehensive Understanding
Read in this order:
1. README.md → Overview
2. DEPLOYMENT_ARCHITECTURE.md → Technical details
3. DEPLOY_TO_TEST.md → Practical deployment

### For Troubleshooting
Check in this order:
1. `docker compose ps` → Service status
2. `docker compose logs` → Error messages
3. **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#troubleshooting)** → Solutions

### For Testing
Follow **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)** systematically

---

## 🆘 Still Need Help?

1. **Check the logs**: `docker compose logs -f`
2. **Verify health**: `curl http://localhost:8000/health`
3. **Review status**: `docker compose ps`
4. **Run checks**: `./preflight_check.sh`
5. **Search docs**: `grep -r "your issue" *.md`

---

## 📋 Documentation Quality

All documentation includes:
- ✅ Clear objectives
- ✅ Step-by-step instructions
- ✅ Code examples
- ✅ Troubleshooting sections
- ✅ Expected outcomes
- ✅ Cross-references

---

**Start here for deployment**: [QUICK_START.md](QUICK_START.md)

**Start here for understanding**: [README.md](README.md)

**Start here for navigation**: You're reading it! 😊
