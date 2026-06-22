package com.repocheck.modules.task.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("task_timeline")
public class TaskTimeline {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long taskId;
    private String status;
    private String message;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
