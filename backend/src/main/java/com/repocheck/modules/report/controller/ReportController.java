package com.repocheck.modules.report.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.repocheck.common.Result;
import com.repocheck.exception.BusinessException;
import com.repocheck.modules.report.dto.BatchExportMarkdownRequest;
import com.repocheck.modules.report.service.ReportService;
import com.repocheck.modules.report.vo.ReportScoreVO;
import com.repocheck.modules.report.vo.ReportVO;
import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/reports")
@RequiredArgsConstructor
public class ReportController {

    private final ReportService reportService;
    private final PaperTaskMapper paperTaskMapper;

    @GetMapping("/{taskId}")
    public Result<ReportVO> getReport(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(reportService.getReport(taskId));
    }

    @GetMapping("/{taskId}/scores")
    public Result<ReportScoreVO> getScores(@PathVariable Long taskId) {
        checkOwnership(taskId);
        return Result.success(reportService.getScores(taskId));
    }

    @PostMapping("/{taskId}/regenerate")
    public Result<Void> regenerate(@PathVariable Long taskId) {
        checkOwnership(taskId);
        reportService.regenerateReport(taskId);
        return Result.success();
    }

    @GetMapping("/{taskId}/export/markdown")
    public ResponseEntity<String> exportMarkdown(@PathVariable Long taskId) {
        checkOwnership(taskId);
        String markdown = reportService.exportMarkdown(taskId);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"repocheck-report-" + taskId + ".md\"")
                .contentType(MediaType.parseMediaType("text/markdown; charset=utf-8"))
                .body(markdown);
    }

    @GetMapping("/{taskId}/export/pdf")
    public ResponseEntity<byte[]> exportPdf(@PathVariable Long taskId) {
        checkOwnership(taskId);
        byte[] pdf = reportService.exportPdf(taskId);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=report-" + taskId + ".pdf")
                .contentType(MediaType.APPLICATION_PDF)
                .body(pdf);
    }

    @PostMapping("/export/markdown/batch")
    public ResponseEntity<byte[]> batchExportMarkdown(@Valid @RequestBody BatchExportMarkdownRequest request) {
        Long userId = StpUtil.getLoginIdAsLong();
        byte[] zipBytes = reportService.batchExportMarkdown(userId, request.getTaskIds());
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"repocheck-reports.zip\"")
                .contentType(MediaType.parseMediaType("application/zip"))
                .body(zipBytes);
    }

    private void checkOwnership(Long taskId) {
        Long userId = StpUtil.getLoginIdAsLong();
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task == null) throw new BusinessException("任务不存在");
        if (!userId.equals(task.getUserId())) throw new BusinessException(403, "无权访问该任务");
    }
}
