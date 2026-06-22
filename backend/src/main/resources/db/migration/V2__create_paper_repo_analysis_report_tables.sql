-- Flyway Migration V2: paper, selected repo, analysis, and report tables.
-- Logical relations:
--   paper_info.task_id -> paper_task.id
--   repo_info.task_id -> paper_task.id
--   repo_analysis.task_id -> paper_task.id
--   report.task_id -> paper_task.id
-- V1 does not use database foreign keys.

CREATE TABLE IF NOT EXISTS `paper_info` (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    arxiv_id VARCHAR(50) DEFAULT NULL,
    title VARCHAR(500) DEFAULT NULL,
    authors TEXT DEFAULT NULL,
    abstract_text TEXT DEFAULT NULL,
    published_at DATE DEFAULT NULL,
    paper_url VARCHAR(500) DEFAULT NULL,
    UNIQUE INDEX uk_task_id (task_id),
    INDEX idx_arxiv_id (arxiv_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `repo_info` (
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
    UNIQUE INDEX uk_task_id (task_id),
    INDEX idx_repo_url (repo_url),
    INDEX idx_owner_repo (owner, repo_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `repo_analysis` (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    has_readme TINYINT DEFAULT 0,
    has_requirements TINYINT DEFAULT 0,
    has_environment_yml TINYINT DEFAULT 0,
    has_dockerfile TINYINT DEFAULT 0,
    has_license TINYINT DEFAULT 0,
    has_train_code TINYINT DEFAULT 0,
    has_inference_code TINYINT DEFAULT 0,
    has_dataset_doc TINYINT DEFAULT 0,
    has_weight_doc TINYINT DEFAULT 0,
    readme_quality_score INT DEFAULT 0,
    dependency_complexity_score INT DEFAULT 0,
    structure_completeness_score INT DEFAULT 0,
    UNIQUE INDEX uk_task_id (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `report` (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    reproducibility_score INT DEFAULT 0,
    completeness_score INT DEFAULT 0,
    environment_score INT DEFAULT 0,
    risk_level VARCHAR(10) DEFAULT NULL,
    summary TEXT DEFAULT NULL,
    method_summary TEXT DEFAULT NULL,
    innovation_summary TEXT DEFAULT NULL,
    reproduce_steps TEXT DEFAULT NULL,
    risk_tips TEXT DEFAULT NULL,
    final_advice TEXT DEFAULT NULL,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX uk_task_id (task_id),
    INDEX idx_risk_level (risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
