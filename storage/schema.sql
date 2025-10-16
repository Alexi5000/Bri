-- BRI Video Agent Database Schema
-- Version: 2.0
-- Last Updated: 2025-10-16

-- Videos table: stores uploaded video metadata
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,  -- Prevent duplicate file paths
    duration REAL NOT NULL,
    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    processing_status TEXT DEFAULT 'pending' NOT NULL,
    thumbnail_path TEXT,
    deleted_at DATETIME,  -- Soft delete support
    CHECK (processing_status IN ('pending', 'processing', 'complete', 'error')),
    CHECK (duration > 0),  -- Duration must be positive
    CHECK (filename != ''),  -- Filename cannot be empty
    CHECK (file_path != '')  -- File path cannot be empty
);

-- Memory table: stores conversation history
CREATE TABLE IF NOT EXISTS memory (
    message_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    CHECK (role IN ('user', 'assistant')),
    CHECK (content != ''),  -- Content cannot be empty
    CHECK (message_id != '')  -- Message ID cannot be empty
);

-- Video context table: stores processed video data (frames, captions, transcripts, objects)
CREATE TABLE IF NOT EXISTS video_context (
    context_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    context_type TEXT NOT NULL,
    timestamp REAL,
    data TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    -- Data lineage fields
    tool_name TEXT,
    tool_version TEXT,
    model_version TEXT,
    processing_params TEXT,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    CHECK (context_type IN ('frame', 'caption', 'transcript', 'object', 'metadata', 'idempotency')),
    CHECK (timestamp IS NULL OR timestamp >= 0),  -- Timestamp must be non-negative if provided
    CHECK (data != ''),  -- Data cannot be empty
    CHECK (context_id != ''),  -- Context ID cannot be empty
    -- Prevent duplicate context entries for same video/type/timestamp
    UNIQUE (video_id, context_type, timestamp, tool_name)
);

-- Data lineage audit table: tracks all data modifications
CREATE TABLE IF NOT EXISTS data_lineage (
    lineage_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    context_id TEXT,
    operation TEXT NOT NULL,
    tool_name TEXT,
    tool_version TEXT,
    model_version TEXT,
    parameters TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id TEXT,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    FOREIGN KEY (context_id) REFERENCES video_context(context_id) ON DELETE SET NULL,
    CHECK (operation IN ('create', 'update', 'delete', 'reprocess')),
    CHECK (lineage_id != '')  -- Lineage ID cannot be empty
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_memory_video_id ON memory(video_id);
CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory(timestamp);
CREATE INDEX IF NOT EXISTS idx_video_context_video_id ON video_context(video_id);
CREATE INDEX IF NOT EXISTS idx_video_context_type ON video_context(context_type);
CREATE INDEX IF NOT EXISTS idx_video_context_timestamp ON video_context(timestamp);
CREATE INDEX IF NOT EXISTS idx_videos_processing_status ON videos(processing_status);
