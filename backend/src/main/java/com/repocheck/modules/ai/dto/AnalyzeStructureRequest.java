package com.repocheck.modules.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AnalyzeStructureRequest {
    private Long taskId;
    private RepoInfoDTO repoInfo;
    private PaperInfoDTO paperInfo;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PaperInfoDTO {
        private String arxivId;
        private String title;
        private String abstractText;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RepoInfoDTO {
        private String platform;
        private String repoUrl;
        private String repoName;
        private String owner;
        private Integer stars;
        private Integer forks;
        private String defaultBranch;
    }
}
