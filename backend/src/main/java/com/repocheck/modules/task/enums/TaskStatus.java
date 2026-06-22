package com.repocheck.modules.task.enums;

import lombok.Getter;

@Getter
public enum TaskStatus {
    PENDING("等待中"),
    PARSING_PAPER("解析论文中"),
    SEARCHING_REPO("搜索仓库中"),
    ANALYZING_REPO("分析仓库中"),
    GENERATING_REPORT("生成报告中"),
    SUCCESS("已完成"),
    FAILED("失败"),
    CANCELLED("已取消");

    private final String label;

    TaskStatus(String label) {
        this.label = label;
    }
}
