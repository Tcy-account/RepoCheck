package com.repocheck.exception;

import cn.dev33.satoken.exception.NotLoginException;
import cn.dev33.satoken.exception.NotPermissionException;
import com.repocheck.common.ErrorCode;
import com.repocheck.common.Result;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.util.stream.Collectors;

/**
 * 全局异常处理
 *
 * 按异常类型分层处理，统一返回 Result 格式。
 * error 日志包含 request URI，业务异常用 warn。
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    // ═══════════════════════════════════════════════════════════
    // 认证与鉴权
    // ═══════════════════════════════════════════════════════════

    @ExceptionHandler(NotLoginException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public Result<?> handleNotLoginException(NotLoginException e, HttpServletRequest req) {
        log.warn("Not logged in: {} [{} {}]", e.getMessage(), req.getMethod(), req.getRequestURI());
        return Result.error(ErrorCode.UNAUTHORIZED.getCode(), ErrorCode.UNAUTHORIZED.getMessage());
    }

    @ExceptionHandler(NotPermissionException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public Result<?> handleNotPermissionException(NotPermissionException e, HttpServletRequest req) {
        log.warn("No permission: {} [{} {}]", e.getMessage(), req.getMethod(), req.getRequestURI());
        return Result.error(ErrorCode.FORBIDDEN.getCode(), ErrorCode.FORBIDDEN.getMessage());
    }

    // ═══════════════════════════════════════════════════════════
    // 业务异常
    // ═══════════════════════════════════════════════════════════

    @ExceptionHandler(BusinessException.class)
    public Result<?> handleBusinessException(BusinessException e, HttpServletRequest req) {
        log.warn("Business exception: [{}] {} [{} {}]", e.getCode(), e.getMessage(),
                req.getMethod(), req.getRequestURI());
        return Result.error(e.getCode(), e.getMessage());
    }

    // ═══════════════════════════════════════════════════════════
    // 参数校验
    // ═══════════════════════════════════════════════════════════

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<?> handleValidation(MethodArgumentNotValidException e, HttpServletRequest req) {
        String details = e.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .collect(Collectors.joining("; "));
        log.warn("Validation failed: {} [{} {}]", details, req.getMethod(), req.getRequestURI());
        return Result.error(ErrorCode.BAD_REQUEST.getCode(),
                ErrorCode.BAD_REQUEST.getMessage() + "：" + details);
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<?> handleMissingParam(MissingServletRequestParameterException e, HttpServletRequest req) {
        log.warn("Missing param: {} [{} {}]", e.getMessage(), req.getMethod(), req.getRequestURI());
        return Result.error(ErrorCode.BAD_REQUEST.getCode(),
                ErrorCode.BAD_REQUEST.getMessage() + "：缺少参数 " + e.getParameterName());
    }

    // ═══════════════════════════════════════════════════════════
    // AI 服务 / 外部 API 网络异常
    // ═══════════════════════════════════════════════════════════

    @ExceptionHandler(ResourceAccessException.class)
    public Result<?> handleResourceAccess(ResourceAccessException e, HttpServletRequest req) {
        Throwable cause = e.getCause();
        String detail;
        if (cause instanceof SocketTimeoutException) {
            detail = "连接超时";
            log.error("AI service timeout [{} {}]", req.getMethod(), req.getRequestURI(), e);
            return Result.error(ErrorCode.AI_SERVICE_TIMEOUT.getCode(),
                    ErrorCode.AI_SERVICE_TIMEOUT.getMessage() + "：" + detail);
        }
        if (cause instanceof ConnectException) {
            detail = "无法连接到 AI 服务";
            log.error("AI service connect failed [{} {}]", req.getMethod(), req.getRequestURI(), e);
            return Result.error(ErrorCode.AI_SERVICE_ERROR.getCode(),
                    ErrorCode.AI_SERVICE_ERROR.getMessage() + "：" + detail);
        }
        detail = "网络异常：" + e.getMessage();
        log.error("Resource access error [{} {}]: {}", req.getMethod(), req.getRequestURI(), detail);
        return Result.error(ErrorCode.EXTERNAL_API_ERROR.getCode(),
                ErrorCode.EXTERNAL_API_ERROR.getMessage() + "：" + detail);
    }

    @ExceptionHandler(RestClientException.class)
    public Result<?> handleRestClient(RestClientException e, HttpServletRequest req) {
        log.error("REST client error [{} {}]: {}", req.getMethod(), req.getRequestURI(), e.getMessage());
        return Result.error(ErrorCode.AI_SERVICE_ERROR.getCode(),
                ErrorCode.AI_SERVICE_ERROR.getMessage() + "：" + e.getMessage());
    }

    // ═══════════════════════════════════════════════════════════
    // 兜底异常
    // ═══════════════════════════════════════════════════════════

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public Result<?> handleException(Exception e, HttpServletRequest req) {
        log.error("Unexpected error [{} {}]", req.getMethod(), req.getRequestURI(), e);
        // 不暴露堆栈给前端
        return Result.error(ErrorCode.INTERNAL_ERROR.getCode(), ErrorCode.INTERNAL_ERROR.getMessage());
    }
}
