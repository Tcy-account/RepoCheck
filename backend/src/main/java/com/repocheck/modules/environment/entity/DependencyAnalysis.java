package com.repocheck.modules.environment.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("dependency_analysis")
public class DependencyAnalysis {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long taskId;
    private String fileType;
    private String filePath;
    private String packageName;
    private String versionSpec;
    private String source;
    private String riskLevel;
    private String riskReason;
    private LocalDateTime createTime;
}
