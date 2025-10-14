-- BRI Video Agent Database Schema

-- Videos table: stores uploaded video metadata
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    duration REAL NOT NULL,
    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',
    thumbnail_path TEXT,
    CHECK (processing_status IN ('pending', 'processing', 'complete', 'error'))
);

-- Memory table: stores conversation history
CREATE TABLE IF NOT EXISTS memory (
    message_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    CHECK (role IN ('user', 'assistant'))
);

-- Video context table: stores processed video data (frames, captions, transcripts, objects)
CREATE TABLE IF NOT EXISTS video_context (
    context_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    context_type TEXT NOT NULL,
    timestamp REAL,
    data TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    CHECK (context_type IN ('frame', 'caption', 'transcript', 'object', 'metadata'))
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_memory_video_id ON memory(video_id);
CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory(timestamp);
CREATE INDEX IF NOT EXISTS idx_video_context_video_id ON video_context(video_id);
CREATE INDEX IF NOT EXISTS idx_video_context_type ON video_context(context_type);
CREATE INDEX IF NOT EXISTS idx_video_context_timestamp ON video_context(timestamp);
CREATE INDEX IF NOT EXISTS idx_videos_processing_status ON videos(processing_status);
