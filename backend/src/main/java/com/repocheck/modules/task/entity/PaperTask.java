package com.repocheck.modules.task.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("paper_task")
public class PaperTask {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String paperUrl;
    private String paperTitle;
    private String status;
    private String errorMessage;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
    private LocalDateTime finishTime;
    /** 逻辑删除：0=正常，1=已删除 */
    @TableLogic
    private Integer deleted;
}
