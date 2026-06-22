package com.repocheck.modules.repo.vo;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class RepoInfoVO {
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
