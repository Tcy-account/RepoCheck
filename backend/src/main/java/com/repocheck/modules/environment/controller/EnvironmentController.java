package com.repocheck.modules.environment.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.repocheck.common.Result;
import com.repocheck.modules.environment.service.EnvironmentService;
import com.repocheck.modules.environment.vo.DependencyAnalysisVO;
import com.repocheck.modules.environment.vo.EnvironmentAnalysisVO;
import com.repocheck.modules.environment.vo.EnvironmentReportVO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/tasks/{taskId}/environment")
@RequiredArgsConstructor
public class EnvironmentController {

    private final EnvironmentService environmentService;

    /** 查询环境分析汇总 */
    @GetMapping
    public Result<EnvironmentAnalysisVO> getEnvironmentAnalysis(@PathVariable Long taskId) {
        StpUtil.checkLogin();
        return Result.success(environmentService.getEnvironmentAnalysis(taskId));
    }

    /** 查询依赖列表 */
    @GetMapping("/dependencies")
    public Result<List<DependencyAnalysisVO>> getDependencies(@PathVariable Long taskId) {
        StpUtil.checkLogin();
        return Result.success(environmentService.getDependencies(taskId));
    }

    /** 重新执行环境分析 */
    @PostMapping("/rebuild")
    public Result<EnvironmentReportVO> rebuildAnalysis(@PathVariable Long taskId) {
        Long userId = StpUtil.getLoginIdAsLong();
        return Result.success(environmentService.rebuildAnalysis(userId, taskId));
    }
}
