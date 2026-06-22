package com.repocheck.modules.analysis.vo;

import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class RepoAnalysisVO {
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
