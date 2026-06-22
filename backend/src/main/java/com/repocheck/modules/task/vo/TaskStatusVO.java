package com.repocheck.modules.task.vo;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class TaskStatusVO {
    private Long taskId;
    private String status;
    private String message;
    private String errorMessage;
    private Boolean finished;
    private LocalDateTime finishTime;
}
