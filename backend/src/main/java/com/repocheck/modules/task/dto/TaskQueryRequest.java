package com.repocheck.modules.task.dto;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class TaskQueryRequest {
    private Integer page = 1;
    private Integer size = 10;
    private String status;
    private String keyword;
    /** 时间范围 — 前端传入 ISO 字符串，Spring 自动绑定到 LocalDateTime */
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    /** 排序字段白名单：createTime / updateTime / finishTime / status */
    private String sortField = "createTime";
    /** asc 或 desc */
    private String sortOrder = "desc";
}
