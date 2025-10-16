# BRI Performance Evaluation Guide

## ✅ All Tests Passing!
- **Unit Tests:** 216/216 passed (100%)
- **Chat Interface Tests:** 14/14 passed (100%)
- **Total:** 230/230 tests passed (100%)

## Running the 50-Question Evaluation

### Step 1: Ensure Video is Processed

1. Open BRI at http://localhost:8502
2. Upload a video or select an existing one
3. Wait for processing to complete (you'll see "✅ Ready to chat!")
4. Note the video ID from the URL or sidebar

### Step 2: Run the Evaluation

```bash
# Run evaluation on a specific video
python tests/eval_bri_performance.py <video_id>

# Example:
python tests/eval_bri_performance.py 75befeed-4502-492c-a62d-d30d1852ef9a
```

### Step 3: Review Results

The evaluation will:
- Ask 50 questions across 5 categories
- Measure response accuracy and speed
- Generate a detailed report

## Evaluation Categories

### 1. Scene Description (10 questions)
- What's happening in the video?
- Describe the setting
- What changes occur?
- Mood and atmosphere
- Visual elements

### 2. Object Detection (15 questions)
- What objects are visible?
- People counting and description
- Vehicles, furniture, animals
- Electronic devices
- Colors and prominent items

### 3. Audio/Transcript (10 questions)
- What is being said?
- Transcription accuracy
- Speaker identification
- Topics discussed
- Tone and emotion

### 4. Timestamp/Temporal (8 questions)
- What happens at specific times?
- Sequence of events
- Duration of scenes
- Changes over time
- Key moments

### 5. General/Context (7 questions)
- Purpose of the video
- Intended audience
- Overall message
- Genre classification
- Emotional impact

## Scoring System

- **Score:** 0.0 to 1.0 based on keyword matching
- **Pass Threshold:** 0.5 (50% of expected keywords found)
- **Categories:** Easy, Medium, Hard difficulty levels

## Report Output

The evaluation generates:

1. **Console Output:**
   - Real-time progress
   - Pass/fail status for each question
   - Summary statistics

2. **JSON Report:** `eval_report_<video_id>.json`
   - Detailed results for all 50 questions
   - Category and difficulty breakdowns
   - Response times
   - Full responses from BRI

## Example Report Structure

```json
{
  "timestamp": "2025-10-16T01:30:00",
  "summary": {
    "total_tests": 50,
    "passed": 42,
    "failed": 8,
    "pass_rate": 0.84,
    "average_score": 0.78,
    "average_response_time": 3.5
  },
  "by_category": {
    "scene": {
      "total": 10,
      "passed": 9,
      "pass_rate": 0.9,
      "avg_score": 0.85
    },
    ...
  },
  "by_difficulty": {
    "easy": {"pass_rate": 0.95},
    "medium": {"pass_rate": 0.82},
    "hard": {"pass_rate": 0.65}
  }
}
```

## Interpreting Results

### Excellent Performance (>85% pass rate)
- BRI accurately understands video content
- Responses are relevant and detailed
- Good coverage across all categories

### Good Performance (70-85% pass rate)
- BRI handles most questions well
- Some categories may need improvement
- Consider reprocessing video or adjusting prompts

### Needs Improvement (<70% pass rate)
- Check if video was fully processed
- Verify video quality and content
- Review failed questions for patterns

## Tips for Best Results

1. **Video Quality:**
   - Use clear, well-lit videos
   - Ensure audio is audible
   - Avoid very long videos (>10 minutes)

2. **Processing:**
   - Wait for full processing completion
   - Check that all tools ran successfully
   - Verify database has stored results

3. **Questions:**
   - Ask specific, clear questions
   - Reference visual or audio elements
   - Use timestamps when relevant

## Troubleshooting

### Low Scores in Scene Category
- Video may not have enough frames extracted
- Try reprocessing with more frames
- Check if captions are being generated

### Low Scores in Audio Category
- Check if audio transcription completed
- Verify audio quality in original video
- Ensure Whisper model is loaded

### Low Scores in Object Category
- Verify YOLO model is detecting objects
- Check if objects are clearly visible
- Review object detection results in logs

## Next Steps

After evaluation:

1. **Review Failed Questions:**
   - Identify patterns in failures
   - Check if specific categories struggle
   - Adjust prompts or processing if needed

2. **Optimize Performance:**
   - Increase frame extraction if needed
   - Adjust confidence thresholds
   - Fine-tune system prompts

3. **Iterate:**
   - Run evaluation on multiple videos
   - Compare results across video types
   - Track improvements over time

## Manual Testing

You can also manually test by:

1. Opening the chat interface
2. Asking questions from the test cases
3. Evaluating responses subjectively
4. Noting any issues or improvements

## Continuous Evaluation

Set up regular evaluations:

```bash
# Create a script to test multiple videos
for video_id in video1 video2 video3; do
    python tests/eval_bri_performance.py $video_id
done
```

## Success Criteria

BRI is performing well if:
- ✅ Overall pass rate > 80%
- ✅ All categories > 70% pass rate
- ✅ Average response time < 5 seconds
- ✅ No crashes or errors during evaluation
- ✅ Responses are coherent and relevant

---

**Ready to evaluate!** Run the evaluation script with your video ID and see how BRI performs! 🎬✨
