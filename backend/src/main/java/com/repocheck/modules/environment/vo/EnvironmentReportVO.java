package com.repocheck.modules.environment.vo;

import lombok.Data;
import java.util.List;

@Data
public class EnvironmentReportVO {
    private Long taskId;
    private EnvironmentAnalysisVO environmentAnalysis;
    private List<DependencyAnalysisVO> dependencies;
}
