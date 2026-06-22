package com.repocheck.modules.task.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import lombok.Data;
import java.util.List;

@Data
public class BatchDeleteTaskRequest {
    @NotEmpty(message = "taskIds 不能为空")
    @Size(max = 50, message = "一次最多删除 50 个任务")
    private List<Long> taskIds;
}
