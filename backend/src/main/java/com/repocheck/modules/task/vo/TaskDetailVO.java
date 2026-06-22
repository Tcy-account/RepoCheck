package com.repocheck.modules.task.vo;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class TaskDetailVO {
    private Long id;
    private Long userId;
    private String paperUrl;
    private String paperTitle;
    private String status;
    private String errorMessage;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    private LocalDateTime finishTime;
}
