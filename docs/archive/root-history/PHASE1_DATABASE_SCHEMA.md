# BRI Database Schema Documentation

Generated: 2025-12-25T18:02:29.799518

## Table: data_lineage
| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| lineage_id | TEXT | False |  | True |
| video_id | TEXT | True |  | False |
| context_id | TEXT | False |  | False |
| operation | TEXT | True |  | False |
| tool_name | TEXT | False |  | False |
| tool_version | TEXT | False |  | False |
| model_version | TEXT | False |  | False |
| parameters | TEXT | False |  | False |
| timestamp | DATETIME | True | CURRENT_TIMESTAMP | False |
| user_id | TEXT | False |  | False |

## Table: memory
| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| message_id | TEXT | False |  | True |
| video_id | TEXT | True |  | False |
| role | TEXT | True |  | False |
| content | TEXT | True |  | False |
| timestamp | DATETIME | True | CURRENT_TIMESTAMP | False |

## Table: schema_version
| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| version | INTEGER | False |  | True |
| description | TEXT | True |  | False |
| applied_at | DATETIME | True | CURRENT_TIMESTAMP | False |
| applied_by | TEXT | False | 'system' | False |

## Table: video_context
| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| context_id | TEXT | False |  | True |
| video_id | TEXT | True |  | False |
| context_type | TEXT | True |  | False |
| timestamp | REAL | False |  | False |
| data | TEXT | True |  | False |
| created_at | DATETIME | True | CURRENT_TIMESTAMP | False |
| tool_name | TEXT | False |  | False |
| tool_version | TEXT | False |  | False |
| model_version | TEXT | False |  | False |
| processing_params | TEXT | False |  | False |

## Table: videos
| Column | Type | Not Null | Default | Primary Key |
|--------|------|----------|---------|-------------|
| video_id | TEXT | False |  | True |
| filename | TEXT | True |  | False |
| file_path | TEXT | True |  | False |
| duration | REAL | True |  | False |
| upload_timestamp | DATETIME | True | CURRENT_TIMESTAMP | False |
| processing_status | TEXT | True | 'pending' | False |
| thumbnail_path | TEXT | False |  | False |
| deleted_at | DATETIME | False |  | False |