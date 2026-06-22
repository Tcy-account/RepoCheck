-- V8: 环境分析 — 依赖清单 + 环境分析汇总

CREATE TABLE dependency_analysis (
    id          BIGINT          AUTO_INCREMENT PRIMARY KEY,
    task_id     BIGINT          NOT NULL,
    file_type   VARCHAR(50)     NOT NULL COMMENT 'requirements / environment_yml / pyproject / dockerfile',
    file_path   VARCHAR(500)    NOT NULL,
    package_name VARCHAR(200)   NOT NULL,
    version_spec VARCHAR(200)   DEFAULT NULL,
    source      VARCHAR(50)     DEFAULT NULL COMMENT 'pip / conda / apt / docker / unknown',
    risk_level  VARCHAR(20)     DEFAULT NULL COMMENT 'LOW / MEDIUM / HIGH',
    risk_reason VARCHAR(500)    DEFAULT NULL,
    create_time DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_task_id      (task_id),
    INDEX idx_package_name (package_name),
    INDEX idx_risk_level   (risk_level),
    INDEX idx_file_type    (file_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='依赖清单分析';

CREATE TABLE environment_analysis (
    id                      BIGINT          AUTO_INCREMENT PRIMARY KEY,
    task_id                 BIGINT          NOT NULL,
    python_version          VARCHAR(100)    DEFAULT NULL,
    cuda_version            VARCHAR(100)    DEFAULT NULL,
    main_framework          VARCHAR(100)    DEFAULT NULL,
    framework_version       VARCHAR(100)    DEFAULT NULL,
    requires_gpu            TINYINT         DEFAULT 0,
    has_docker              TINYINT         DEFAULT 0,
    docker_base_image       VARCHAR(300)    DEFAULT NULL,
    dependency_risk_score   INT             DEFAULT 0,
    cuda_risk_score         INT             DEFAULT 0,
    docker_readiness_score  INT             DEFAULT 0,
    environment_score       INT             DEFAULT 0,
    risk_level              VARCHAR(20)     DEFAULT NULL COMMENT 'LOW / MEDIUM / HIGH',
    risk_summary            TEXT            DEFAULT NULL,
    install_advice          TEXT            DEFAULT NULL,
    create_time             DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time             DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_task_id       (task_id),
    INDEX      idx_risk_level    (risk_level),
    INDEX      idx_main_framework (main_framework)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='环境分析汇总';
