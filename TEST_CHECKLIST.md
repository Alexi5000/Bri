# BRI Video Agent - Testing Checklist

Use this checklist to systematically test the deployed application.

## Pre-Test Setup

- [ ] Application is deployed and running
- [ ] All three services show as healthy: `docker compose ps`
- [ ] Can access http://localhost:8501 in browser
- [ ] Have test videos ready (MP4 format, 30-60 seconds recommended)

## Basic Functionality Tests

### 1. Welcome Screen
- [ ] Welcome screen loads correctly
- [ ] BRI branding/logo is visible
- [ ] "Get Started" or upload button is present
- [ ] No error messages displayed

### 2. Video Upload
- [ ] Can click upload button
- [ ] File picker opens
- [ ] Can select a video file
- [ ] Upload progress is shown
- [ ] Video appears in library after upload
- [ ] Video player displays the video

### 3. Video Processing
- [ ] Processing status is shown
- [ ] Progress indicator updates
- [ ] Processing completes successfully
- [ ] No error messages during processing
- [ ] Time taken is reasonable (< 2 minutes for 1-minute video)

### 4. Video Player
- [ ] Video plays correctly
- [ ] Play/pause button works
- [ ] Seek bar works
- [ ] Volume control works
- [ ] Fullscreen option works (if available)
- [ ] Video quality is acceptable

## Query Testing

### 5. Visual Description Queries
- [ ] Ask: "What's happening in this video?"
  - [ ] Get a response within 5 seconds
  - [ ] Response describes visual content
  - [ ] Response includes timestamps
  - [ ] Timestamps are clickable
  - [ ] Frame thumbnails are shown (if applicable)

- [ ] Ask: "Describe what you see at the beginning"
  - [ ] Get relevant response
  - [ ] Response focuses on early part of video

- [ ] Ask: "What happens at the end?"
  - [ ] Get relevant response
  - [ ] Response focuses on later part of video

### 6. Audio Transcription Queries
- [ ] Ask: "What did they say?"
  - [ ] Get transcription
  - [ ] Transcription is accurate (or reasonable)
  - [ ] Includes timestamps

- [ ] Ask: "Transcribe the audio"
  - [ ] Get full or partial transcript
  - [ ] Formatted clearly

- [ ] Ask: "What was said at 0:30?"
  - [ ] Get transcript for that time range
  - [ ] Timestamp is accurate

### 7. Object Detection Queries
- [ ] Ask: "What objects can you detect?"
  - [ ] Get list of detected objects
  - [ ] Objects are reasonable/accurate
  - [ ] Confidence scores shown (if applicable)

- [ ] Ask: "Are there any people in the video?"
  - [ ] Get yes/no response
  - [ ] If yes, details about people shown

- [ ] Ask: "What things are visible?"
  - [ ] Get description of visible objects
  - [ ] Response is comprehensive

### 8. Timestamp Navigation
- [ ] Click a timestamp in a response
  - [ ] Video seeks to that time
  - [ ] Video starts playing (or is ready to play)
  - [ ] Timestamp is accurate (±2 seconds acceptable)

- [ ] Click multiple timestamps
  - [ ] Each navigation works correctly
  - [ ] No lag or errors

### 9. Follow-up Questions
- [ ] After initial query, ask follow-up
  - [ ] System remembers context
  - [ ] Response is relevant to conversation
  - [ ] Can chain 3-4 questions

- [ ] Test follow-ups:
  - "Tell me more about that"
  - "What else?"
  - "Can you elaborate?"
  - [ ] All work correctly

### 10. Conversation History
- [ ] Ask multiple questions
- [ ] Can see previous questions and answers
- [ ] History is maintained during session
- [ ] Can scroll through history
- [ ] History is formatted clearly

## Advanced Features

### 11. Multiple Videos
- [ ] Upload a second video
- [ ] Both videos appear in library
- [ ] Can switch between videos
- [ ] Conversations are separate per video
- [ ] No confusion between videos

### 12. Video Library
- [ ] All uploaded videos are listed
- [ ] Can click/select videos
- [ ] Video metadata is shown (if applicable):
  - [ ] Video name
  - [ ] Duration
  - [ ] Upload date
  - [ ] Processing status

### 13. Error Handling
- [ ] Try uploading invalid file (e.g., .txt)
  - [ ] Get friendly error message
  - [ ] App doesn't crash

- [ ] Ask nonsensical question
  - [ ] Get reasonable response or error
  - [ ] App continues working

- [ ] Disconnect internet briefly
  - [ ] App handles gracefully
  - [ ] Shows appropriate error

### 14. Performance
- [ ] First video processing: < 2 minutes
- [ ] Subsequent queries: < 5 seconds
- [ ] Timestamp navigation: < 1 second
- [ ] UI is responsive (no lag)
- [ ] Memory usage is reasonable

### 15. Edge Cases
- [ ] Upload very short video (5-10 seconds)
  - [ ] Processes successfully
  - [ ] Can still query

- [ ] Upload longer video (2-3 minutes)
  - [ ] Processes (may take longer)
  - [ ] Can still query

- [ ] Ask very long question
  - [ ] Gets response
  - [ ] No character limit error

- [ ] Ask very short question (1-2 words)
  - [ ] Gets reasonable response

## System Health

### 16. Service Status
```bash
docker compose ps
```
- [ ] All services show "healthy" or "running"
- [ ] No services are restarting repeatedly

### 17. Logs Check
```bash
docker compose logs --tail=100
```
- [ ] No critical errors
- [ ] No repeated warnings
- [ ] Processing logs look normal

```bash
docker compose logs mcp-server --tail=50
```
- [ ] Models loaded successfully
- [ ] Tools registered
- [ ] No errors

```bash
docker compose logs streamlit-ui --tail=50
```
- [ ] App started successfully
- [ ] No connection errors

### 18. Resource Usage
```bash
docker stats
```
- [ ] Memory usage < 4GB total
- [ ] CPU usage reasonable (< 50% average)
- [ ] No runaway processes

### 19. Health Endpoints
```bash
curl http://localhost:8000/health
```
- [ ] Returns 200 OK
- [ ] Response shows healthy status

```bash
curl http://localhost:8000/docs
```
- [ ] API documentation loads
- [ ] Endpoints are listed

### 20. Data Persistence
- [ ] Stop and restart services:
  ```bash
  docker compose down
  docker compose up -d
  ```
- [ ] Videos still in library
- [ ] Can query videos again
- [ ] Data persists

## Test Scenarios

### Scenario 1: New User Experience (5 min)
- [ ] Open app as new user
- [ ] Upload first video
- [ ] Wait for processing
- [ ] Ask 2-3 questions
- [ ] Experience is smooth and intuitive

### Scenario 2: Power User (10 min)
- [ ] Upload 3 different videos
- [ ] Switch between them
- [ ] Ask complex questions
- [ ] Test all query types
- [ ] Use timestamp navigation extensively

### Scenario 3: Error Recovery (5 min)
- [ ] Cause errors (invalid uploads, etc.)
- [ ] App recovers gracefully
- [ ] Can continue normal operations

### Scenario 4: Performance Test (10 min)
- [ ] Process multiple videos back-to-back
- [ ] Ask rapid-fire questions
- [ ] Monitor response times
- [ ] Check for slowdowns

## Issues Found

Document any issues here:

### Critical Issues (Prevent usage)
- [ ] Issue 1: 
- [ ] Issue 2:

### Major Issues (Significant impact)
- [ ] Issue 1:
- [ ] Issue 2:

### Minor Issues (Small annoyances)
- [ ] Issue 1:
- [ ] Issue 2:

### Suggestions for Improvement
- [ ] Suggestion 1:
- [ ] Suggestion 2:

## Performance Metrics

Record actual performance:

- First video upload time: ______ seconds
- Video processing time: ______ seconds
- First query response time: ______ seconds
- Subsequent query response: ______ seconds
- Timestamp navigation time: ______ seconds
- Memory usage: ______ GB
- CPU usage: ______ %

## Test Summary

Date: ________________
Tester: ________________
Duration: ________________

### Overall Assessment
- [ ] All critical functionality works
- [ ] Performance is acceptable
- [ ] User experience is good
- [ ] Ready for wider testing
- [ ] Needs fixes before proceeding

### Recommendation
- [ ] Approve for next phase
- [ ] Minor fixes needed
- [ ] Major fixes required
- [ ] Not ready

### Notes
_______________________________________________________________________
_______________________________________________________________________
_______________________________________________________________________
_______________________________________________________________________

## Next Steps

Based on test results:

1. [ ] Document all issues in issue tracker
2. [ ] Prioritize fixes
3. [ ] Plan improvements
4. [ ] Schedule next test cycle
5. [ ] Update documentation as needed

---

**Testing completed**: ☐ Yes  ☐ No  
**Ready for production**: ☐ Yes  ☐ No  ☐ With fixes
