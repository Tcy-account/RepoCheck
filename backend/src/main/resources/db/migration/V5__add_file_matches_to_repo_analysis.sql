ALTER TABLE repo_analysis
ADD COLUMN file_matches_json JSON DEFAULT NULL COMMENT 'Matched repository files grouped by analysis category';
