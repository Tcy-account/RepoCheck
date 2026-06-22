package com.repocheck.modules.repo.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("repo_candidate")
public class RepoCandidate {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long taskId;
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
    private String source;
    private Integer selected;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
