package com.repocheck.modules.task.vo;

import lombok.Data;
import java.util.List;

@Data
public class BatchDeleteTaskResponse {
    private int successCount;
    private int failedCount;
    private List<BatchDeleteTaskResultVO> results;
}
