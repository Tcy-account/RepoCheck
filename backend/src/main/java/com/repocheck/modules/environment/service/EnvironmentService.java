package com.repocheck.modules.environment.service;

import com.repocheck.modules.environment.vo.DependencyAnalysisVO;
import com.repocheck.modules.environment.vo.EnvironmentAnalysisVO;
import com.repocheck.modules.environment.vo.EnvironmentReportVO;
import java.util.List;

public interface EnvironmentService {
    /** 查询环境分析汇总 */
    EnvironmentAnalysisVO getEnvironmentAnalysis(Long taskId);

    /** 查询依赖列表 */
    List<DependencyAnalysisVO> getDependencies(Long taskId);

    /** 重新执行环境分析（同步调用 ai-service，更新数据库） */
    EnvironmentReportVO rebuildAnalysis(Long userId, Long taskId);
}
