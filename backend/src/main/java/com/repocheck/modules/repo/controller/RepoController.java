package com.repocheck.modules.repo.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.repocheck.common.Result;
import com.repocheck.exception.BusinessException;
import com.repocheck.modules.repo.dto.UpdateRepoRequest;
import com.repocheck.modules.repo.service.RepoService;
import com.repocheck.modules.repo.vo.RepoCandidateVO;
import com.repocheck.modules.repo.vo.RepoInfoVO;
import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/tasks/{taskId}/repo")
@RequiredArgsConstructor
public class RepoController {

    private final RepoService repoService;
    private final PaperTaskMapper paperTaskMapper;

    @GetMapping
    public Result<RepoInfoVO> getRepo(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(repoService.getRepoInfo(taskId));
    }

    @GetMapping("/candidates")
    public Result<Map<String, Object>> getCandidates(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(Map.of("candidates", repoService.getCandidates(taskId)));
    }

    @PutMapping
    public Result<Void> updateRepo(@PathVariable Long taskId, @Valid @RequestBody UpdateRepoRequest request) {
        checkOwnership(taskId);
        repoService.updateRepo(taskId, request);
        return Result.success();
    }

    @PostMapping("/search")
    public Result<Void> searchRepo(@PathVariable Long taskId) {
        checkOwnership(taskId);
        repoService.searchRepo(taskId);
        return Result.success();
    }

    private void checkOwnership(Long taskId) {
        Long userId = StpUtil.getLoginIdAsLong();
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task == null) throw new BusinessException("任务不存在");
        if (!userId.equals(task.getUserId())) throw new BusinessException(403, "无权访问该任务");
    }
}
