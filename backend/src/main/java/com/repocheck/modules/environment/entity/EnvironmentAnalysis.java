package com.repocheck.modules.environment.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("environment_analysis")
public class EnvironmentAnalysis {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long taskId;
    private String pythonVersion;
    private String cudaVersion;
    private String mainFramework;
    private String frameworkVersion;
    private Integer requiresGpu;
    private Integer hasDocker;
    private String dockerBaseImage;
    private Integer dependencyRiskScore;
    private Integer cudaRiskScore;
    private Integer dockerReadinessScore;
    private Integer environmentScore;
    private String riskLevel;
    private String riskSummary;
    private String installAdvice;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
