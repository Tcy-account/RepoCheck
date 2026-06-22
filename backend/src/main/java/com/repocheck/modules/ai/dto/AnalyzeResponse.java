package com.repocheck.modules.ai.dto;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;

@Data
public class AnalyzeResponse {
    private Long taskId;
    private PaperInfoDTO paperInfo;
    private RepoInfoDTO repoInfo;
    private RepoAnalysisDTO repoAnalysis;
    private ReportDTO report;

    @Data
    public static class PaperInfoDTO {
        private String arxivId;
        private String title;
        private String authors;
        private String abstractText;
        private LocalDate publishedAt;
        private String paperUrl;
    }

    @Data
    public static class RepoInfoDTO {
        private String platform;
        private String repoUrl;
        private String repoName;
        private String owner;
        private Integer stars;
        private Integer forks;
        private String defaultBranch;
        private LocalDateTime lastUpdatedAt;
        private BigDecimal confidence;
        private String confidenceReason;
    }

    @Data
    public static class RepoAnalysisDTO {
        private Boolean hasReadme;
        private Boolean hasRequirements;
        private Boolean hasEnvironmentYml;
        private Boolean hasDockerfile;
        private Boolean hasLicense;
        private Boolean hasTrainCode;
        private Boolean hasInferenceCode;
        private Boolean hasDatasetDoc;
        private Boolean hasWeightDoc;
        private Integer readmeQualityScore;
        private Integer dependencyComplexityScore;
        private Integer structureCompletenessScore;
        private Map<String, Object> fileMatches;
        private Map<String, Object> readmeAnalysis;
    }

    @Data
    public static class ReportDTO {
        private Integer reproducibilityScore;
        private Integer completenessScore;
        private Integer environmentScore;
        private String riskLevel;
        private String summary;
        private String methodSummary;
        private String innovationSummary;
        private String reproduceSteps;
        private String riskTips;
        private String finalAdvice;
    }
}
