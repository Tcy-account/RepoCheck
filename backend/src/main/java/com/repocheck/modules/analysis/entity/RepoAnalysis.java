package com.repocheck.modules.analysis.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("repo_analysis")
public class RepoAnalysis {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long taskId;
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
    private String fileMatchesJson;
    private String readmeAnalysisJson;
}
