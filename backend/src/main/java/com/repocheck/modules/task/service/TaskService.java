package com.repocheck.modules.task.service;

import com.repocheck.common.PageResult;
import com.repocheck.modules.task.dto.CreateTaskRequest;
import com.repocheck.modules.task.dto.TaskQueryRequest;
import com.repocheck.modules.task.vo.*;

import java.util.List;

public interface TaskService {
    Long createTask(Long userId, CreateTaskRequest request);
    PageResult<TaskVO> listTasks(Long userId, TaskQueryRequest query);
    TaskDetailVO getTask(Long id);
    TaskStatusVO getTaskStatus(Long id);
    TaskTimelineVO getTaskTimeline(Long id);
    void retryTask(Long id);
    void cancelTask(Long id);
    void deleteTask(Long id);
    BatchDeleteTaskResponse batchDeleteTasks(Long userId, List<Long> taskIds);
}
