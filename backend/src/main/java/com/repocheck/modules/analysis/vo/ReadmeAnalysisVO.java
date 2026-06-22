package com.repocheck.modules.analysis.vo;

import lombok.Data;

@Data
public class ReadmeAnalysisVO {
    private Boolean hasInstallSection;
    private Boolean hasTrainSection;
    private Boolean hasInferenceSection;
    private Boolean hasDatasetSection;
    private Boolean hasWeightSection;
    private Boolean hasCitationSection;
    private Boolean hasExampleCommands;
    private Integer readmeLength;
    private Integer readmeQualityScore;
}
