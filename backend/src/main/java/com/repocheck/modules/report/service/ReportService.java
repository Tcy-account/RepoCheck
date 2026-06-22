package com.repocheck.modules.report.service;

import com.repocheck.modules.report.vo.ReportVO;
import com.repocheck.modules.report.vo.ReportScoreVO;

import java.util.List;

public interface ReportService {
    ReportVO getReport(Long taskId);
    ReportScoreVO getScores(Long taskId);
    void regenerateReport(Long taskId);
    String exportMarkdown(Long taskId);
    byte[] exportPdf(Long taskId);
    byte[] batchExportMarkdown(Long userId, List<Long> taskIds);
}
