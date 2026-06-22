package com.repocheck.modules.environment.vo;

import lombok.Data;

@Data
public class EnvironmentAnalysisVO {
    private Long taskId;
    private String pythonVersion;
    private String cudaVersion;
    private String mainFramework;
    private String frameworkVersion;
    private Boolean requiresGpu;
    private Boolean hasDocker;
    private String dockerBaseImage;
    private Integer dependencyRiskScore;
    private Integer cudaRiskScore;
    private Integer dockerReadinessScore;
    private Integer environmentScore;
    private String riskLevel;
    private String riskSummary;
    private String installAdvice;
}
