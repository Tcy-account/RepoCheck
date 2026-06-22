package com.repocheck.modules.task.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.repocheck.common.PageResult;
import com.repocheck.common.Result;
import com.repocheck.exception.BusinessException;
import com.repocheck.modules.task.dto.BatchDeleteTaskRequest;
import com.repocheck.modules.task.dto.CreateTaskRequest;
import com.repocheck.modules.task.dto.TaskQueryRequest;
import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import com.repocheck.modules.task.service.TaskService;
import com.repocheck.modules.task.vo.*;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/tasks")
@RequiredArgsConstructor
public class TaskController {

    private final TaskService taskService;
    private final PaperTaskMapper paperTaskMapper;

    @PostMapping
    public Result<Map<String, Long>> createTask(@Valid @RequestBody CreateTaskRequest request) {
        Long userId = StpUtil.getLoginIdAsLong();
        Long taskId = taskService.createTask(userId, request);
        return Result.success(Map.of("taskId", taskId));
    }

    @GetMapping
    public Result<PageResult<TaskVO>> listTasks(TaskQueryRequest query) {
        Long userId = StpUtil.getLoginIdAsLong();
        return Result.success(taskService.listTasks(userId, query));
    }

    @GetMapping("/{taskId}")
    public Result<TaskDetailVO> getTask(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(taskService.getTask(taskId));
    }

    @GetMapping("/{taskId}/status")
    public Result<TaskStatusVO> getStatus(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(taskService.getTaskStatus(taskId));
    }

    @GetMapping("/{taskId}/timeline")
    public Result<TaskTimelineVO> getTimeline(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(taskService.getTaskTimeline(taskId));
    }

    @PostMapping("/{taskId}/retry")
    public Result<Void> retry(@PathVariable Long taskId) {
        checkOwnership(taskId);
        taskService.retryTask(taskId);
        return Result.success();
    }

    @PostMapping("/{taskId}/cancel")
    public Result<Void> cancel(@PathVariable Long taskId) {
        checkOwnership(taskId);
        taskService.cancelTask(taskId);
        return Result.success();
    }

    @DeleteMapping("/{taskId}")
    public Result<Void> delete(@PathVariable Long taskId) {
        checkOwnership(taskId);
        taskService.deleteTask(taskId);
        return Result.success();
    }

    @PostMapping("/batch-delete")
    public Result<BatchDeleteTaskResponse> batchDelete(@Valid @RequestBody BatchDeleteTaskRequest request) {
        Long userId = StpUtil.getLoginIdAsLong();
        return Result.success(taskService.batchDeleteTasks(userId, request.getTaskIds()));
    }

    /** 校验任务归属当前登录用户 */
    private void checkOwnership(Long taskId) {
        Long userId = StpUtil.getLoginIdAsLong();
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task == null) {
            throw new BusinessException("任务不存在");
        }
        if (!userId.equals(task.getUserId())) {
            throw new BusinessException(403, "无权访问该任务");
        }
    }
}
