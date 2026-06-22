package com.repocheck.modules.environment.vo;

import lombok.Data;

@Data
public class DependencyAnalysisVO {
    private Long id;
    private Long taskId;
    private String fileType;
    private String filePath;
    private String packageName;
    private String versionSpec;
    private String source;
    private String riskLevel;
    private String riskReason;
}
