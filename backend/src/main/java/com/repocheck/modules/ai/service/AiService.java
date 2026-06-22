package com.repocheck.modules.ai.service;

import com.repocheck.modules.ai.dto.AnalyzeEnvironmentRequest;
import com.repocheck.modules.ai.dto.AnalyzeEnvironmentResponse;
import com.repocheck.modules.ai.dto.AnalyzeResponse;
import com.repocheck.modules.ai.dto.AnalyzeStructureRequest;
import com.repocheck.modules.ai.dto.GenerateReportRequest;
import com.repocheck.modules.task.enums.TaskStatus;

public interface AiService {
    void analyzeTask(Long taskId, String paperUrl);
    AnalyzeResponse analyzeStructure(AnalyzeStructureRequest request);
    AnalyzeResponse generateReportData(GenerateReportRequest request);
    AnalyzeEnvironmentResponse analyzeEnvironment(AnalyzeEnvironmentRequest request);

    void saveOrUpdateResults(Long taskId, AnalyzeResponse response);
    void recordTimeline(Long taskId, TaskStatus status, String message);
    void updateStatus(Long taskId, TaskStatus status, String errorMessage);
}
