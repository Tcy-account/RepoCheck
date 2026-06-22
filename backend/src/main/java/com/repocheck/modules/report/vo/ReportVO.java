package com.repocheck.modules.report.vo;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Data
public class ReportVO {
    private PaperInfoVO paperInfo;
    private RepoInfoVO repoInfo;
    private RepoAnalysisVO repoAnalysis;
    private ReportDataVO report;

    @Data
    public static class PaperInfoVO {
        private String arxivId;
        private String title;
        private String authors;
        private String abstractText;
        private LocalDate publishedAt;
        private String paperUrl;
    }

    @Data
    public static class RepoInfoVO {
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
    public static class RepoAnalysisVO {
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
        private Map<String, List<String>> fileMatches;
        private Map<String, Object> readmeAnalysis;
    }

    @Data
    public static class ReportDataVO {
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
