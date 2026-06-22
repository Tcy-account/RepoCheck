package com.repocheck.modules.task.vo;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;

@Data
public class TaskTimelineVO {
    private Long taskId;
    private List<StatusEntry> timeline;

    @Data
    public static class StatusEntry {
        private Long id;
        private Long taskId;
        private String status;
        private String message;
        private LocalDateTime createTime;
    }
}
