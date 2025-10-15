# Video Processing Tools

This directory contains the video processing tools used by BRI for multimodal video analysis.

## Available Tools

### 1. Frame Extractor (`frame_extractor.py`)
Extracts frames from videos using OpenCV.

**Features:**
- Extract frames at regular intervals
- Extract specific frames at timestamps
- Adaptive interval calculation based on video length
- Video metadata retrieval (duration, fps, resolution, codec)

**Usage:**
```python
from tools.frame_extractor import FrameExtractor

extractor = FrameExtractor()
frames = extractor.extract_frames(
    video_path="path/to/video.mp4",
    video_id="video_123",
    interval_seconds=2.0,
    max_frames=100
)
```

### 2. Image Captioner (`image_captioner.py`)
Generates natural language descriptions of video frames using BLIP.

**Features:**
- Single frame captioning
- Efficient batch processing (10 frames at a time)
- Confidence scoring for captions
- Automatic fallback to individual processing if batch fails
- Graceful error handling with placeholder captions

**Model:** Salesforce/blip-image-captioning-large

**Usage:**
```python
from tools.image_captioner import ImageCaptioner

captioner = ImageCaptioner()

# Single frame
caption = captioner.caption_frame(
    image_path="path/to/frame.jpg",
    timestamp=2.5
)
print(f"Caption: {caption.text} (confidence: {caption.confidence})")

# Batch processing
captions = captioner.caption_frames_batch(
    image_paths=["frame1.jpg", "frame2.jpg", "frame3.jpg"],
    timestamps=[0.0, 2.0, 4.0]
)
```

### 3. Audio Transcriber (`audio_transcriber.py`)
Transcribes audio from videos using OpenAI Whisper.

**Features:**
- Full video transcription with timestamps
- Segment transcription for specific time ranges
- Automatic language detection (99 languages supported)
- Confidence scoring for transcriptions
- Direct video file support (no need to extract audio)

**Model:** OpenAI Whisper (base model by default)

**Usage:**
```python
from tools.audio_transcriber import AudioTranscriber

transcriber = AudioTranscriber(model_size="base")

# Full video transcription
transcript = transcriber.transcribe_video("path/to/video.mp4")
print(f"Language: {transcript.language}")
print(f"Full text: {transcript.full_text}")

# Display segments with timestamps
for segment in transcript.segments:
    print(f"[{segment.start:.2f}s - {segment.end:.2f}s]: {segment.text}")

# Transcribe specific time range
segment = transcriber.transcribe_segment(
    video_path="path/to/video.mp4",
    start_time=10.0,
    end_time=20.0
)
print(f"Segment: {segment.text}")
```

### 4. Object Detector (`object_detector.py`)
Detects and tracks objects in video frames using YOLOv8.

**Features:**
- Batch object detection across multiple frames
- Search for specific object classes
- Single frame detection
- Bounding box coordinates and confidence scores
- Support for 80 COCO object classes

**Model:** YOLOv8n (optimized for speed)

**Usage:**
```python
from tools.object_detector import ObjectDetector

detector = ObjectDetector(model_name="yolov8n.pt")

# Batch detection
detections = detector.detect_objects_in_frames(
    frame_paths=["frame1.jpg", "frame2.jpg"],
    timestamps=[0.0, 2.5],
    confidence_threshold=0.3
)

# Search for specific object
dog_frames = detector.search_for_object(
    frame_paths=frame_paths,
    timestamps=timestamps,
    object_class="dog",
    confidence_threshold=0.3
)

# Get available classes
classes = detector.get_available_classes()
print(f"Can detect: {', '.join(classes[:10])}...")
```

## Testing

### Testing Object Detector

To test the Object Detector tool:

```bash
python scripts/test_object_detector.py
```

The test script will:
- Initialize the YOLOv8 model
- Extract frames from a test video
- Test batch object detection
- Test object search functionality
- Test single frame detection
- Display available object classes

**Note:** First run will download the YOLOv8n model (~6MB), which should be quick.

### Testing Audio Transcriber

To test the Audio Transcriber tool:

```bash
python scripts/test_audio_transcriber.py
```

The test script will:
- Initialize the Whisper model
- Test full video transcription (if test video exists)
- Test segment transcription (if test video exists)
- Display language, segments, and transcript text

**Note:** First run will download the Whisper model (~140MB for base), which may take a minute.

### Testing Image Captioner

To test the Image Captioner tool:

1. **Ensure you have frames extracted:**
   ```bash
   python scripts/test_frame_extractor.py
   ```

2. **Run the captioner test:**
   ```bash
   python scripts/test_image_captioner.py
   ```

The test script will:
- Initialize the BLIP model
- Test single frame captioning
- Test batch frame captioning
- Verify error handling

**Note:** First run will download the BLIP model (~2GB), which may take a few minutes.

### Manual Testing

You can also test manually in Python:

```python
from tools.image_captioner import ImageCaptioner
from tools.frame_extractor import FrameExtractor

# Extract frames from a video
extractor = FrameExtractor()
frames = extractor.extract_frames(
    video_path="data/videos/sample.mp4",
    video_id="test_video",
    max_frames=5
)

# Caption the frames
captioner = ImageCaptioner()
image_paths = [frame.image_path for frame in frames]
timestamps = [frame.timestamp for frame in frames]

captions = captioner.caption_frames_batch(image_paths, timestamps)

for caption in captions:
    print(f"[{caption.frame_timestamp}s] {caption.text}")
```

## Performance Considerations

### Object Detector
- **Model Size:** yolov8n (~6MB), yolov8s (~22MB), yolov8m (~52MB), yolov8l (~88MB), yolov8x (~136MB)
- **Processing Speed:** ~50-100 FPS on GPU, ~5-10 FPS on CPU
- **GPU Acceleration:** Automatically uses CUDA if available
- **Memory:** yolov8n requires ~500MB RAM during processing
- **Classes:** Detects 80 COCO classes (person, car, dog, cat, etc.)

### Audio Transcriber
- **Model Size:** base (~140MB), small (~240MB), medium (~770MB), large (~1.5GB)
- **Processing Speed:** ~1x realtime on CPU (1 min video = ~1 min processing)
- **GPU Acceleration:** 5-10x faster with CUDA
- **Memory:** base model requires ~500MB RAM during processing
- **Languages:** Supports 99 languages with automatic detection

### Image Captioner
- **GPU Acceleration:** Automatically uses CUDA if available
- **Batch Size:** Processes 10 frames at a time for optimal performance
- **Memory:** BLIP model requires ~2GB GPU memory or ~4GB RAM
- **Speed:** ~1-2 seconds per frame on CPU, ~0.1-0.3 seconds on GPU

### Optimization Tips
1. Use batch processing for multiple frames (10x faster than individual)
2. Enable GPU acceleration for significant speedup
3. Consider using smaller BLIP model for faster inference:
   - `Salesforce/blip-image-captioning-base` (faster, slightly less accurate)
   - `Salesforce/blip-image-captioning-large` (default, best quality)
4. For object detection, use yolov8n for speed or yolov8m/l for accuracy
5. Adjust confidence thresholds to balance precision vs recall

## Error Handling

All tools implement graceful error handling:

- **Missing files:** Raises `FileNotFoundError` with clear message
- **Invalid inputs:** Raises `ValueError` with explanation
- **Processing failures:** Returns placeholder results and logs errors
- **Batch failures:** Falls back to individual processing

## Dependencies

See `requirements.txt` for full list. Key dependencies:

- **Frame Extractor:** opencv-python
- **Image Captioner:** transformers, torch, pillow
- **Audio Transcriber:** openai-whisper
- **Object Detector:** ultralytics

## Model Downloads

On first use, models will be automatically downloaded:

- **BLIP:** ~2GB (Hugging Face cache: `~/.cache/huggingface/`)
- **Whisper:** 
  - tiny: ~40MB
  - base: ~140MB (default)
  - small: ~240MB
  - medium: ~770MB
  - large: ~1.5GB
- **YOLO:** 
  - yolov8n: ~6MB (default, fastest)
  - yolov8s: ~22MB
  - yolov8m: ~52MB
  - yolov8l: ~88MB
  - yolov8x: ~136MB (most accurate)

## Troubleshooting

### BLIP Model Loading Issues

If you encounter issues loading the BLIP model:

```python
# Try using the base model instead
captioner = ImageCaptioner(model_name="Salesforce/blip-image-captioning-base")
```

### Out of Memory Errors

If you get OOM errors:

1. Reduce batch size in `_process_batch` method
2. Use CPU instead of GPU (automatic fallback)
3. Use smaller model variant

### Slow Performance

1. Ensure GPU is being used (check with `torch.cuda.is_available()`)
2. Use batch processing instead of individual frames
3. Consider using base model for faster inference

## Contributing

When adding new tools:

1. Follow the existing interface patterns
2. Implement proper error handling
3. Add confidence scores where applicable
4. Support batch processing for efficiency
5. Add tests in `scripts/test_<tool_name>.py`
6. Update this README with usage examples
