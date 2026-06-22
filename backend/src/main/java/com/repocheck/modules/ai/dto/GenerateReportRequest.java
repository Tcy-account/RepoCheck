package com.repocheck.modules.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class GenerateReportRequest {
    private Long taskId;
    private Map<String, Object> paperInfo;
    private Map<String, Object> repoInfo;
    private Map<String, Object> repoAnalysis;
    private Map<String, Object> scoreDetails;
}
