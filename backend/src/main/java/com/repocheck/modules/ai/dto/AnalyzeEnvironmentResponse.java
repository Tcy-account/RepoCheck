package com.repocheck.modules.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

/**
 * 环境分析响应 — ai-service POST /api/environment/analyze 返回
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AnalyzeEnvironmentResponse {
    private Long taskId;
    private List<DependencyDTO> dependencies;
    private EnvironmentDTO environmentAnalysis;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DependencyDTO {
        private String fileType;
        private String filePath;
        private String packageName;
        private String versionSpec;
        private String source;
        private String riskLevel;
        private String riskReason;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class EnvironmentDTO {
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
}
