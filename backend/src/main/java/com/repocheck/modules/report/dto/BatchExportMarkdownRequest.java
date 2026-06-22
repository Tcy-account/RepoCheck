package com.repocheck.modules.report.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import lombok.Data;
import java.util.List;

@Data
public class BatchExportMarkdownRequest {
    @NotEmpty(message = "taskIds 不能为空")
    @Size(max = 20, message = "一次最多导出 20 个报告")
    private List<Long> taskIds;
}
