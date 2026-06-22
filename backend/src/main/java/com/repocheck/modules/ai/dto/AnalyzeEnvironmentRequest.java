package com.repocheck.modules.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 环境分析请求 — 传给 ai-service POST /api/environment/analyze
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AnalyzeEnvironmentRequest {
    private Long taskId;
    private RepoInfoDTO repoInfo;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RepoInfoDTO {
        private String platform;
        private String repoUrl;
        private String repoName;
        private String owner;
        private String defaultBranch;
    }
}
