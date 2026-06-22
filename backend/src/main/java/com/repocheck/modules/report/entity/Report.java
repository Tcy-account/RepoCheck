package com.repocheck.modules.report.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("report")
public class Report {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long taskId;
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
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
