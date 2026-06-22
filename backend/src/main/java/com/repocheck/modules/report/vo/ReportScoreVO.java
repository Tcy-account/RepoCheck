package com.repocheck.modules.report.vo;

import lombok.Data;

@Data
public class ReportScoreVO {
    private Integer reproducibilityScore;
    private Integer completenessScore;
    private Integer environmentScore;
    private String riskLevel;
}
