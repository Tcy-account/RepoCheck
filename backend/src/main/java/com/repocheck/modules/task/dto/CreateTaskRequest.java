package com.repocheck.modules.task.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CreateTaskRequest {
    @NotBlank(message = "论文链接不能为空")
    private String paperUrl;
}
