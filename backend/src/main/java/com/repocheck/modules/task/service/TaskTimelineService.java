package com.repocheck.modules.task.service;

import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.entity.TaskTimeline;
import com.repocheck.modules.task.enums.TaskStatus;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import com.repocheck.modules.task.mapper.TaskTimelineMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

/**
 * 统一的任务状态与时间线服务
 *
 * 所有模块通过本服务更新 paper_task.status 和 task_timeline，
 * 避免散落的 updateStatus / recordTimeline。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TaskTimelineService {

    private final PaperTaskMapper paperTaskMapper;
    private final TaskTimelineMapper taskTimelineMapper;

    /**
     * 更新任务状态并写入时间线
     *
     * @param taskId       任务 ID
     * @param status       新状态
     * @param message      时间线消息（可为 null，此时取 TaskStatus.label）
     */
    @Transactional
    public void updateTaskStatus(Long taskId, TaskStatus status, String message) {
        // 1. 更新 paper_task
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task == null) {
            log.warn("updateTaskStatus: task {} not found", taskId);
            return;
        }
        task.setStatus(status.name());
        task.setUpdateTime(LocalDateTime.now());

        // 终态：写入 finishTime
        if (isTerminal(status)) {
            task.setFinishTime(LocalDateTime.now());
        }

        // 失败时写入 errorMessage
        if (status == TaskStatus.FAILED && message != null) {
            task.setErrorMessage(message);
        }

        paperTaskMapper.updateById(task);

        // 2. 写入 timeline
        String timelineMsg = (message != null) ? message : status.getLabel();
        TaskTimeline tl = new TaskTimeline();
        tl.setTaskId(taskId);
        tl.setStatus(status.name());
        tl.setMessage(timelineMsg);
        taskTimelineMapper.insert(tl);

        log.info("Task {} status → {}: {}", taskId, status.name(), timelineMsg);
    }

    /**
     * 写入时间线记录（不改变任务状态）
     */
    @Transactional
    public void recordTimeline(Long taskId, TaskStatus status, String message) {
        String timelineMsg = (message != null) ? message : status.getLabel();
        TaskTimeline tl = new TaskTimeline();
        tl.setTaskId(taskId);
        tl.setStatus(status.name());
        tl.setMessage(timelineMsg);
        taskTimelineMapper.insert(tl);
        log.info("Task {} timeline: {} - {}", taskId, status.name(), timelineMsg);
    }

    /**
     * 判断是否为终态
     */
    public static boolean isTerminal(TaskStatus status) {
        return status == TaskStatus.SUCCESS
                || status == TaskStatus.FAILED
                || status == TaskStatus.CANCELLED;
    }

    /**
     * 判断是否为终态（按字符串）
     */
    public static boolean isTerminal(String status) {
        return TaskStatus.SUCCESS.name().equals(status)
                || TaskStatus.FAILED.name().equals(status)
                || TaskStatus.CANCELLED.name().equals(status);
    }
}
