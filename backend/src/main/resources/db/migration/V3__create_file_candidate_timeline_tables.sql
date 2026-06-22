-- Flyway Migration V3: file, repo candidate, and task timeline tables.
-- Logical relations:
--   file_info.task_id -> paper_task.id
--   repo_candidate.task_id -> paper_task.id
--   task_timeline.task_id -> paper_task.id
-- V1 does not use database foreign keys.

CREATE TABLE IF NOT EXISTS `file_info` (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    file_id VARCHAR(64) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT DEFAULT 0,
    file_type VARCHAR(30) DEFAULT NULL,
    minio_path VARCHAR(500) DEFAULT NULL,
    task_id BIGINT DEFAULT NULL,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX uk_file_id (file_id),
    INDEX idx_task_id (task_id),
    INDEX idx_file_type (file_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `repo_candidate` (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    platform VARCHAR(20) DEFAULT NULL,
    repo_url VARCHAR(500) DEFAULT NULL,
    repo_name VARCHAR(200) DEFAULT NULL,
    owner VARCHAR(200) DEFAULT NULL,
    stars INT DEFAULT 0,
    forks INT DEFAULT 0,
    default_branch VARCHAR(100) DEFAULT NULL,
    last_updated_at DATETIME DEFAULT NULL,
    confidence DECIMAL(5,4) DEFAULT 0.0000,
    confidence_reason VARCHAR(500) DEFAULT NULL,
    source VARCHAR(50) DEFAULT NULL,
    selected TINYINT DEFAULT 0,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_repo_url (repo_url),
    INDEX idx_selected (selected)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `task_timeline` (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    status VARCHAR(30) NOT NULL,
    message VARCHAR(500) DEFAULT NULL,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
