package com.repocheck.modules.task.vo;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class TaskVO {
    private Long id;
    private String paperTitle;
    private String paperUrl;
    private String status;
    private String errorMessage;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    private LocalDateTime finishTime;
}
