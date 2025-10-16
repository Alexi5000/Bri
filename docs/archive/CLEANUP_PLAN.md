# Root Directory Cleanup Plan

## Files to Move/Organize

### Analysis Files (Move to docs/archive/)
- ARCHITECTURE_ANALYSIS.md
- DATA_ENGINEERING_ANALYSIS.md
- EVALUATION_GUIDE.md
- LOGGING_IMPLEMENTATION.md
- PHASE5_SUMMARY.md
- README_PHASE4.md
- STYLING_IMPROVEMENTS.md
- STYLING_TEST_CHECKLIST.md
- TASK_ORDER_CHANGES.md
- TEST_RESULTS.md

### Execution/Deployment Guides (Keep in docs/)
- DEPLOYMENT.md
- WINDOWS_DEPLOYMENT_GUIDE.md
- START_BRI_WINDOWS.md
- QUICKSTART.md
- EXECUTE_THIS.md
- EXECUTION_PLAN.md

### Utility Scripts (Move to scripts/utils/)
- analyze_failures.py
- analyze_passing.py
- check_video_context.py
- check_videos.py
- diagnose_system.py
- get_videos.py
- list_videos.py
- process_test_video.py
- quick_fix.py

### Evaluation Reports (Move to data/evaluations/)
- eval_report_--help.json
- eval_report_75befeed.json
- eval_report_978ea94d.json
- eval_report_test-vid.json

### Keep in Root
- app.py (main entry point)
- config.py (configuration)
- requirements.txt (dependencies)
- README.md (main readme)
- INDEX.md (project index)
- FINAL_TASK_SUMMARY.md (important summary)
- TASK_EXECUTION_ORDER.md (important reference)
- .env, .env.example (configuration)
- .gitignore, .dockerignore (git/docker config)
- docker-compose.yml, Dockerfile.* (docker config)
- yolov8n.pt (model file - should stay or move to models/)

### Files to Delete (Redundant/Obsolete)
- LAYOUT_FIXES.md (merged into other docs)
- QUICK_DATA_FIXES.md (temporary fix doc)
