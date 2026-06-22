ALTER TABLE paper_task
ADD COLUMN deleted TINYINT NOT NULL DEFAULT 0 COMMENT 'Logic delete flag: 0 active, 1 deleted';

CREATE INDEX idx_deleted ON paper_task(deleted);
CREATE INDEX idx_user_deleted ON paper_task(user_id, deleted);
