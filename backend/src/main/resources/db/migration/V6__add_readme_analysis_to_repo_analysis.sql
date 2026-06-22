ALTER TABLE repo_analysis
    ADD COLUMN readme_analysis_json JSON DEFAULT NULL COMMENT 'README section analysis result';
