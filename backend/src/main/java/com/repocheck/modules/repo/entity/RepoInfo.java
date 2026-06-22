package com.repocheck.modules.repo.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("repo_info")
public class RepoInfo {
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
}
