package com.repocheck.modules.task.vo;

import lombok.Data;

@Data
public class BatchDeleteTaskResultVO {
    private Long taskId;
    private boolean success;
    private String message;

    public static BatchDeleteTaskResultVO ok(Long taskId) {
        BatchDeleteTaskResultVO r = new BatchDeleteTaskResultVO();
        r.taskId = taskId;
        r.success = true;
        r.message = "删除成功";
        return r;
    }

    public static BatchDeleteTaskResultVO fail(Long taskId, String message) {
        BatchDeleteTaskResultVO r = new BatchDeleteTaskResultVO();
        r.taskId = taskId;
        r.success = false;
        r.message = message;
        return r;
    }
}
