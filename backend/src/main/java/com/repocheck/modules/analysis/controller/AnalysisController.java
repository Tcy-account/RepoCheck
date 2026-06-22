package com.repocheck.modules.analysis.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.repocheck.common.Result;
import com.repocheck.exception.BusinessException;
import com.repocheck.modules.analysis.service.AnalysisService;
import com.repocheck.modules.analysis.vo.ReadmeAnalysisVO;
import com.repocheck.modules.analysis.vo.RepoAnalysisVO;
import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/tasks/{taskId}/analysis")
@RequiredArgsConstructor
public class AnalysisController {

    private final AnalysisService analysisService;
    private final PaperTaskMapper paperTaskMapper;

    @GetMapping
    public Result<RepoAnalysisVO> getAnalysis(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(analysisService.getAnalysis(taskId));
    }

    @PostMapping("/rebuild")
    public Result<Void> rebuild(@PathVariable Long taskId) {
        checkOwnership(taskId);
        analysisService.rebuildAnalysis(taskId);
        return Result.success();
    }

    @GetMapping("/files")
    public Result<Map<String, Object>> getFiles(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(Map.of("files", analysisService.getFileList(taskId)));
    }

    @GetMapping("/readme")
    public Result<ReadmeAnalysisVO> getReadme(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(analysisService.getReadmeAnalysis(taskId));
    }

    private void checkOwnership(Long taskId) {
        Long userId = StpUtil.getLoginIdAsLong();
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task == null) throw new BusinessException("任务不存在");
        if (!userId.equals(task.getUserId())) throw new BusinessException(403, "无权访问该任务");
    }
}
