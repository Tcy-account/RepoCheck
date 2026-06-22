package com.repocheck.exception;

import com.repocheck.common.ErrorCode;
import lombok.Getter;

/**
 * 业务异常
 *
 * 支持三种构造方式：
 *   1. 仅 ErrorCode           — 使用枚举预定义 message
 *   2. ErrorCode + 自定义 msg  — 覆盖默认 message
 *   3. ErrorCode + msg + cause — 携带原始异常
 */
@Getter
public class BusinessException extends RuntimeException {

    private final int code;

    /** 仅使用 ErrorCode 的预定义 message */
    public BusinessException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.code = errorCode.getCode();
    }

    /** ErrorCode + 自定义 message */
    public BusinessException(ErrorCode errorCode, String message) {
        super(message);
        this.code = errorCode.getCode();
    }

    /** ErrorCode + 自定义 message + 原始异常 */
    public BusinessException(ErrorCode errorCode, String message, Throwable cause) {
        super(message, cause);
        this.code = errorCode.getCode();
    }

    // ── 向后兼容 ──

    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }

    public BusinessException(String message) {
        super(message);
        this.code = ErrorCode.INTERNAL_ERROR.getCode();
    }
}
