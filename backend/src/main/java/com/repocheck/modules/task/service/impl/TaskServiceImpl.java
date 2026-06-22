package com.repocheck.modules.task.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.support.SFunction;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.repocheck.common.PageResult;
import com.repocheck.exception.BusinessException;
import com.repocheck.modules.ai.service.AiService;
import com.repocheck.modules.task.dto.CreateTaskRequest;
import com.repocheck.modules.task.dto.TaskQueryRequest;
import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.entity.TaskTimeline;
import com.repocheck.modules.task.enums.TaskStatus;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import com.repocheck.modules.task.mapper.TaskTimelineMapper;
import com.repocheck.modules.task.service.TaskService;
import com.repocheck.modules.task.service.TaskTimelineService;
import com.repocheck.modules.task.vo.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class TaskServiceImpl implements TaskService {

    private final PaperTaskMapper paperTaskMapper;
    private final TaskTimelineMapper taskTimelineMapper;
    private final TaskTimelineService taskTimelineService;
    private final AiService aiService;

    /** 排序字段白名单：前端名 → Lambda 列引用（防 SQL 注入） */
    private static final Map<String, SFunction<PaperTask, ?>> SORT_COLUMN_MAP = Map.of(
            "createTime", PaperTask::getCreateTime,
            "updateTime", PaperTask::getUpdateTime,
            "finishTime", PaperTask::getFinishTime,
            "status", PaperTask::getStatus
    );

    @Override
    public Long createTask(Long userId, CreateTaskRequest request) {
        PaperTask task = new PaperTask();
        task.setUserId(userId);
        task.setPaperUrl(request.getPaperUrl());
        task.setStatus(TaskStatus.PENDING.name());
        paperTaskMapper.insert(task);

        taskTimelineService.recordTimeline(task.getId(), TaskStatus.PENDING, "任务已创建，等待分析");

        triggerAnalysis(task.getId(), request.getPaperUrl());
        return task.getId();
    }

    @Async
    protected void triggerAnalysis(Long taskId, String paperUrl) {
        try {
            aiService.analyzeTask(taskId, paperUrl);
        } catch (Exception e) {
            log.error("Unhandled error in triggerAnalysis for task {}", taskId, e);
        }
    }

    @Override
    public PageResult<TaskVO> listTasks(Long userId, TaskQueryRequest query) {
        // 参数归一化
        int page = Math.max(query.getPage() != null ? query.getPage() : 1, 1);
        int size = Math.min(Math.max(query.getSize() != null ? query.getSize() : 10, 1), 100);
        String keyword = query.getKeyword() != null ? query.getKeyword().trim() : null;

        LambdaQueryWrapper<PaperTask> wrapper = new LambdaQueryWrapper<>();
        // 1. 用户归属
        wrapper.eq(PaperTask::getUserId, userId);
        // 2. 状态筛选
        if (query.getStatus() != null && !query.getStatus().isEmpty()) {
            wrapper.eq(PaperTask::getStatus, query.getStatus());
        }
        // 3. 关键词模糊匹配（标题或链接）
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.and(w -> w
                    .like(PaperTask::getPaperTitle, keyword)
                    .or()
                    .like(PaperTask::getPaperUrl, keyword));
        }
        // 4. 时间范围
        if (query.getStartTime() != null) {
            wrapper.ge(PaperTask::getCreateTime, query.getStartTime());
        }
        if (query.getEndTime() != null) {
            wrapper.le(PaperTask::getCreateTime, query.getEndTime());
        }
        // 5. 排序（白名单）
        applySorting(wrapper, query.getSortField(), query.getSortOrder());

        Page<PaperTask> pageResult = paperTaskMapper.selectPage(
                new Page<>(page, size), wrapper);

        List<TaskVO> records = pageResult.getRecords().stream()
                .map(this::toTaskVO).collect(Collectors.toList());
        return PageResult.of(records, pageResult.getTotal(), page, size);
    }

    /** 白名单排序，非法字段使用默认 createTime desc */
    private void applySorting(LambdaQueryWrapper<PaperTask> wrapper, String sortField, String sortOrder) {
        SFunction<PaperTask, ?> column = SORT_COLUMN_MAP.getOrDefault(
                sortField, PaperTask::getCreateTime);
        boolean asc = "asc".equalsIgnoreCase(sortOrder);
        if (asc) {
            wrapper.orderByAsc(column);
        } else {
            wrapper.orderByDesc(column);
        }
    }

    @Override
    public TaskDetailVO getTask(Long id) {
        PaperTask task = getPaperTask(id);
        return toDetailVO(task);
    }

    @Override
    public TaskStatusVO getTaskStatus(Long id) {
        PaperTask task = getPaperTask(id);
        TaskStatusVO vo = new TaskStatusVO();
        vo.setTaskId(task.getId());
        vo.setStatus(task.getStatus());
        vo.setErrorMessage(task.getErrorMessage());
        vo.setFinished(TaskTimelineService.isTerminal(task.getStatus()));
        vo.setFinishTime(task.getFinishTime());

        List<TaskTimeline> entries = taskTimelineMapper.selectList(
                new LambdaQueryWrapper<TaskTimeline>()
                        .eq(TaskTimeline::getTaskId, id)
                        .orderByDesc(TaskTimeline::getCreateTime)
                        .last("LIMIT 1"));
        if (!entries.isEmpty()) {
            vo.setMessage(entries.get(0).getMessage());
        }
        return vo;
    }

    @Override
    public TaskTimelineVO getTaskTimeline(Long id) {
        PaperTask task = getPaperTask(id);
        TaskTimelineVO vo = new TaskTimelineVO();
        vo.setTaskId(task.getId());

        List<TaskTimeline> entries = taskTimelineMapper.selectList(
                new LambdaQueryWrapper<TaskTimeline>()
                        .eq(TaskTimeline::getTaskId, id)
                        .orderByAsc(TaskTimeline::getCreateTime));

        List<TaskTimelineVO.StatusEntry> timeline = new ArrayList<>();
        for (TaskTimeline tl : entries) {
            TaskTimelineVO.StatusEntry e = new TaskTimelineVO.StatusEntry();
            e.setId(tl.getId());
            e.setTaskId(tl.getTaskId());
            e.setStatus(tl.getStatus());
            e.setMessage(tl.getMessage());
            e.setCreateTime(tl.getCreateTime());
            timeline.add(e);
        }
        vo.setTimeline(timeline);
        return vo;
    }

    @Override
    public void retryTask(Long id) {
        PaperTask task = getPaperTask(id);
        String s = task.getStatus();
        if (!TaskStatus.FAILED.name().equals(s)
                && !TaskStatus.CANCELLED.name().equals(s)) {
            throw new BusinessException("只能重试失败或已取消的任务");
        }

        task.setStatus(TaskStatus.PENDING.name());
        task.setErrorMessage(null);
        task.setUpdateTime(LocalDateTime.now());
        task.setFinishTime(null);
        paperTaskMapper.updateById(task);

        taskTimelineService.recordTimeline(task.getId(), TaskStatus.PENDING,
                "任务已重新提交，等待分析");
        triggerAnalysis(task.getId(), task.getPaperUrl());
    }

    @Override
    public void cancelTask(Long id) {
        PaperTask task = getPaperTask(id);
        String s = task.getStatus();

        if (TaskTimelineService.isTerminal(task.getStatus())) {
            throw new BusinessException("任务已完成或已取消，无法再次取消");
        }

        taskTimelineService.updateTaskStatus(task.getId(), TaskStatus.CANCELLED,
                "任务已取消");
    }

    @Override
    public void deleteTask(Long id) {
        PaperTask task = getPaperTask(id);
        String s = task.getStatus();

        // 进行中的任务不允许直接删除，需先取消
        if (!TaskTimelineService.isTerminal(s)) {
            throw new BusinessException("任务正在分析中，请取消后再删除");
        }

        // 逻辑删除（@TableLogic 会让 deleteById 自动 set deleted=1）
        paperTaskMapper.deleteById(id);

        taskTimelineService.recordTimeline(id, TaskStatus.valueOf(s), "任务已删除");
    }

    @Override
    public BatchDeleteTaskResponse batchDeleteTasks(Long userId, List<Long> taskIds) {
        List<BatchDeleteTaskResultVO> results = new ArrayList<>();
        int success = 0, failed = 0;

        for (Long taskId : taskIds) {
            try {
                PaperTask task = paperTaskMapper.selectById(taskId);
                if (task == null) {
                    results.add(BatchDeleteTaskResultVO.fail(taskId, "任务不存在"));
                    failed++;
                    continue;
                }
                if (!userId.equals(task.getUserId())) {
                    results.add(BatchDeleteTaskResultVO.fail(taskId, "任务不存在或无权限"));
                    failed++;
                    continue;
                }
                String s = task.getStatus();
                if (!TaskTimelineService.isTerminal(s)) {
                    results.add(BatchDeleteTaskResultVO.fail(taskId, "任务正在分析中，请取消后再删除"));
                    failed++;
                    continue;
                }
                paperTaskMapper.deleteById(taskId);
                taskTimelineService.recordTimeline(taskId, TaskStatus.valueOf(s), "任务已删除");
                results.add(BatchDeleteTaskResultVO.ok(taskId));
                success++;
            } catch (Exception e) {
                log.error("batchDeleteTasks error for taskId={}: {}", taskId, e.getMessage());
                results.add(BatchDeleteTaskResultVO.fail(taskId, "删除失败: " + e.getMessage()));
                failed++;
            }
        }

        BatchDeleteTaskResponse resp = new BatchDeleteTaskResponse();
        resp.setSuccessCount(success);
        resp.setFailedCount(failed);
        resp.setResults(results);
        return resp;
    }

    private PaperTask getPaperTask(Long id) {
        PaperTask task = paperTaskMapper.selectById(id);
        if (task == null) throw new BusinessException("任务不存在");
        return task;
    }

    private TaskVO toTaskVO(PaperTask task) {
        TaskVO vo = new TaskVO();
        vo.setId(task.getId());
        vo.setPaperTitle(task.getPaperTitle());
        vo.setPaperUrl(task.getPaperUrl());
        vo.setStatus(task.getStatus());
        vo.setErrorMessage(task.getErrorMessage());
        vo.setCreateTime(task.getCreateTime());
        vo.setUpdateTime(task.getUpdateTime());
        vo.setFinishTime(task.getFinishTime());
        return vo;
    }

    private TaskDetailVO toDetailVO(PaperTask task) {
        TaskDetailVO vo = new TaskDetailVO();
        vo.setId(task.getId());
        vo.setUserId(task.getUserId());
        vo.setPaperUrl(task.getPaperUrl());
        vo.setPaperTitle(task.getPaperTitle());
        vo.setStatus(task.getStatus());
        vo.setErrorMessage(task.getErrorMessage());
        vo.setCreateTime(task.getCreateTime());
        vo.setUpdateTime(task.getUpdateTime());
        vo.setFinishTime(task.getFinishTime());
        return vo;
    }
}
