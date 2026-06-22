-- ============================================================
-- RepoCheck V1.0 数据库初始化脚本
-- ============================================================
-- ⚠️ 此文件仅作为历史初始化参考，已不再使用。
-- 项目真实数据库版本管理以 backend/src/main/resources/db/migration 下的
-- Flyway 迁移脚本为准。详情见 backend/README.md 和 docs/architecture.md。
-- ============================================================

CREATE DATABASE IF NOT EXISTS repocheck DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE repocheck;

-- 用户表
CREATE TABLE IF NOT EXISTS user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码 (加密)',
    email VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 论文检测任务表
CREATE TABLE IF NOT EXISTS paper_task (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    paper_url VARCHAR(500) NOT NULL COMMENT 'arXiv 论文链接',
    paper_title VARCHAR(500) DEFAULT NULL COMMENT '论文标题',
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING' COMMENT '任务状态',
    error_message TEXT DEFAULT NULL COMMENT '错误信息',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    finish_time DATETIME DEFAULT NULL COMMENT '完成时间',
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='论文检测任务表';

-- 论文信息表
CREATE TABLE IF NOT EXISTS paper_info (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL UNIQUE COMMENT '关联任务 ID',
    arxiv_id VARCHAR(50) DEFAULT NULL COMMENT 'arXiv ID',
    title VARCHAR(500) DEFAULT NULL COMMENT '论文标题',
    authors TEXT DEFAULT NULL COMMENT '作者列表',
    abstract_text TEXT DEFAULT NULL COMMENT '摘要',
    published_at DATE DEFAULT NULL COMMENT '发布日期',
    paper_url VARCHAR(500) DEFAULT NULL COMMENT '论文链接',
    INDEX idx_arxiv_id (arxiv_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='论文信息表';

-- 代码仓库信息表
CREATE TABLE IF NOT EXISTS repo_info (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL UNIQUE COMMENT '关联任务 ID',
    platform VARCHAR(20) DEFAULT NULL COMMENT '平台: GitHub / GitLab',
    repo_url VARCHAR(500) DEFAULT NULL COMMENT '仓库 URL',
    repo_name VARCHAR(200) DEFAULT NULL COMMENT '仓库名称',
    owner VARCHAR(200) DEFAULT NULL COMMENT '仓库所有者',
    stars INT DEFAULT 0 COMMENT 'Star 数量',
    forks INT DEFAULT 0 COMMENT 'Fork 数量',
    default_branch VARCHAR(100) DEFAULT NULL COMMENT '默认分支',
    last_updated_at DATETIME DEFAULT NULL COMMENT '最后更新时间',
    confidence DECIMAL(3,2) DEFAULT 0.00 COMMENT '置信度',
    confidence_reason VARCHAR(500) DEFAULT NULL COMMENT '置信度理由'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代码仓库信息表';

-- 仓库分析结果表
CREATE TABLE IF NOT EXISTS repo_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL UNIQUE COMMENT '关联任务 ID',
    has_readme TINYINT DEFAULT 0 COMMENT '是否有 README',
    has_requirements TINYINT DEFAULT 0 COMMENT '是否有 requirements.txt',
    has_environment_yml TINYINT DEFAULT 0 COMMENT '是否有 environment.yml',
    has_dockerfile TINYINT DEFAULT 0 COMMENT '是否有 Dockerfile',
    has_license TINYINT DEFAULT 0 COMMENT '是否有 LICENSE',
    has_train_code TINYINT DEFAULT 0 COMMENT '是否有训练代码',
    has_inference_code TINYINT DEFAULT 0 COMMENT '是否有推理代码',
    has_dataset_doc TINYINT DEFAULT 0 COMMENT '是否有数据集说明',
    has_weight_doc TINYINT DEFAULT 0 COMMENT '是否有模型权重说明',
    readme_quality_score INT DEFAULT 0 COMMENT 'README 质量评分',
    dependency_complexity_score INT DEFAULT 0 COMMENT '依赖复杂度评分',
    structure_completeness_score INT DEFAULT 0 COMMENT '结构完整度评分'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='仓库分析结果表';

-- 报告表
CREATE TABLE IF NOT EXISTS report (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL UNIQUE COMMENT '关联任务 ID',
    reproducibility_score INT DEFAULT 0 COMMENT '复现难度评分',
    completeness_score INT DEFAULT 0 COMMENT '仓库完整度评分',
    environment_score INT DEFAULT 0 COMMENT '环境复杂度评分',
    risk_level VARCHAR(10) DEFAULT NULL COMMENT '风险等级',
    summary TEXT DEFAULT NULL COMMENT 'AI 总结报告',
    method_summary TEXT DEFAULT NULL COMMENT '方法总结',
    innovation_summary TEXT DEFAULT NULL COMMENT '创新点总结',
    reproduce_steps TEXT DEFAULT NULL COMMENT '复现步骤',
    risk_tips TEXT DEFAULT NULL COMMENT '风险提示',
    final_advice TEXT DEFAULT NULL COMMENT '最终建议',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告表';

-- 文件信息表
CREATE TABLE IF NOT EXISTS file_info (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    file_id VARCHAR(64) NOT NULL UNIQUE COMMENT '文件 UUID',
    file_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小 (字节)',
    file_type VARCHAR(30) DEFAULT NULL COMMENT '文件类型: REPORT_PDF / REPORT_MD / PAPER_PDF / LOG',
    minio_path VARCHAR(500) DEFAULT NULL COMMENT 'MinIO 存储路径',
    task_id BIGINT DEFAULT NULL COMMENT '关联任务 ID',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_task_id (task_id),
    INDEX idx_file_id (file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件信息表';
