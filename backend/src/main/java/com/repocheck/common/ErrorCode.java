package com.repocheck.common;

import lombok.Getter;

/**
 * 统一错误码
 *
 * 规则：
 * - HTTP 标准码 (1xx-5xx) 用于通用错误
 * - 1xxx 业务码用于任务相关
 * - 2xxx 业务码用于报告相关
 * - 3xxx 业务码用于仓库/输入校验
 * - 4xxx 业务码用于 AI 服务与外部 API
 */
@Getter
public enum ErrorCode {

    // ── HTTP 通用 ──
    SUCCESS(200, "success"),
    BAD_REQUEST(400, "请求参数错误"),
    UNAUTHORIZED(401, "未登录或登录已过期"),
    FORBIDDEN(403, "无权限访问"),
    NOT_FOUND(404, "资源不存在"),
    CONFLICT(409, "业务冲突"),
    INTERNAL_ERROR(500, "服务器内部错误"),
    NOT_IMPLEMENTED(501, "功能尚未实现"),

    // ── 任务 (1xxx) ──
    TASK_NOT_FOUND(1001, "任务不存在"),
    TASK_NOT_READY(1002, "任务尚未完成"),
    TASK_ALREADY_CANCELLED(1003, "任务已取消"),
    TASK_RUNNING(1004, "任务正在分析中"),

    // ── 报告 (2xxx) ──
    REPORT_NOT_FOUND(2001, "报告不存在或尚未生成"),

    // ── 仓库 / 输入校验 (3xxx) ──
    REPO_URL_INVALID(3001, "请输入合法的 GitHub 仓库链接"),
    ARXIV_URL_INVALID(3002, "请输入合法的 arXiv 论文链接"),

    // ── AI 服务与外部 API (4xxx) ──
    AI_SERVICE_ERROR(4001, "AI 服务调用失败"),
    AI_SERVICE_TIMEOUT(4002, "AI 服务调用超时"),
    EXTERNAL_API_ERROR(4003, "外部 API 调用失败");

    private final int code;
    private final String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }
}
