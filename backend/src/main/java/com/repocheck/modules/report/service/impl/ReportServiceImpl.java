package com.repocheck.modules.report.service.impl;

import com.repocheck.exception.BusinessException;
import com.repocheck.modules.ai.dto.AnalyzeResponse;
import com.repocheck.modules.ai.dto.GenerateReportRequest;
import com.repocheck.modules.ai.service.AiService;
import com.repocheck.modules.analysis.entity.RepoAnalysis;
import com.repocheck.modules.analysis.mapper.RepoAnalysisMapper;
import com.repocheck.modules.environment.entity.DependencyAnalysis;
import com.repocheck.modules.environment.entity.EnvironmentAnalysis;
import com.repocheck.modules.environment.mapper.DependencyAnalysisMapper;
import com.repocheck.modules.environment.mapper.EnvironmentAnalysisMapper;
import com.repocheck.modules.paper.entity.PaperInfo;
import com.repocheck.modules.paper.mapper.PaperInfoMapper;
import com.repocheck.modules.repo.entity.RepoInfo;
import com.repocheck.modules.repo.mapper.RepoInfoMapper;
import com.repocheck.modules.report.entity.Report;
import com.repocheck.modules.report.mapper.ReportMapper;
import com.repocheck.modules.report.service.ReportService;
import com.repocheck.modules.report.util.MarkdownReportBuilder;
import com.repocheck.modules.report.vo.ReportScoreVO;
import com.repocheck.modules.report.vo.ReportVO;
import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReportServiceImpl implements ReportService {

    private final PaperInfoMapper paperInfoMapper;
    private final RepoInfoMapper repoInfoMapper;
    private final RepoAnalysisMapper repoAnalysisMapper;
    private final ReportMapper reportMapper;
    private final PaperTaskMapper paperTaskMapper;
    private final EnvironmentAnalysisMapper environmentAnalysisMapper;
    private final DependencyAnalysisMapper dependencyAnalysisMapper;
    private final AiService aiService;
    private final ObjectMapper objectMapper;

    @Override
    public ReportVO getReport(Long taskId) {
        Report report = getReportByTaskId(taskId);
        return buildReportVO(taskId, report);
    }

    private ReportVO buildReportVO(Long taskId, Report report) {
        ReportVO vo = new ReportVO();
        // 论文信息
        PaperInfo pi = paperInfoMapper.selectOne(new LambdaQueryWrapper<PaperInfo>().eq(PaperInfo::getTaskId, taskId));
        if (pi != null) {
            ReportVO.PaperInfoVO piv = new ReportVO.PaperInfoVO();
            piv.setArxivId(pi.getArxivId()); piv.setTitle(pi.getTitle());
            piv.setAuthors(pi.getAuthors()); piv.setAbstractText(pi.getAbstractText());
            piv.setPublishedAt(pi.getPublishedAt()); piv.setPaperUrl(pi.getPaperUrl());
            vo.setPaperInfo(piv);
        }
        // 仓库信息
        RepoInfo ri = repoInfoMapper.selectOne(new LambdaQueryWrapper<RepoInfo>().eq(RepoInfo::getTaskId, taskId));
        if (ri != null) {
            ReportVO.RepoInfoVO riv = new ReportVO.RepoInfoVO();
            riv.setPlatform(ri.getPlatform()); riv.setRepoUrl(ri.getRepoUrl());
            riv.setRepoName(ri.getRepoName()); riv.setOwner(ri.getOwner());
            riv.setStars(ri.getStars()); riv.setForks(ri.getForks());
            riv.setDefaultBranch(ri.getDefaultBranch()); riv.setLastUpdatedAt(ri.getLastUpdatedAt());
            riv.setConfidence(ri.getConfidence()); riv.setConfidenceReason(ri.getConfidenceReason());
            vo.setRepoInfo(riv);
        }
        // 分析结果
        RepoAnalysis ra = repoAnalysisMapper.selectOne(new LambdaQueryWrapper<RepoAnalysis>().eq(RepoAnalysis::getTaskId, taskId));
        if (ra != null) {
            ReportVO.RepoAnalysisVO rav = new ReportVO.RepoAnalysisVO();
            rav.setHasReadme(ra.getHasReadme()); rav.setHasRequirements(ra.getHasRequirements());
            rav.setHasEnvironmentYml(ra.getHasEnvironmentYml()); rav.setHasDockerfile(ra.getHasDockerfile());
            rav.setHasLicense(ra.getHasLicense()); rav.setHasTrainCode(ra.getHasTrainCode());
            rav.setHasInferenceCode(ra.getHasInferenceCode()); rav.setHasDatasetDoc(ra.getHasDatasetDoc());
            rav.setHasWeightDoc(ra.getHasWeightDoc());
            rav.setReadmeQualityScore(ra.getReadmeQualityScore());
            rav.setDependencyComplexityScore(ra.getDependencyComplexityScore());
            rav.setStructureCompletenessScore(ra.getStructureCompletenessScore());
            // 解析 file_matches_json
            if (ra.getFileMatchesJson() != null && !ra.getFileMatchesJson().isEmpty()) {
                try {
                    Map<String, List<String>> fm = objectMapper.readValue(
                            ra.getFileMatchesJson(), new TypeReference<Map<String, List<String>>>() {});
                    rav.setFileMatches(fm);
                } catch (Exception e) {
                    log.warn("Failed to parse fileMatchesJson for taskId={}: {}", taskId, e.getMessage());
                }
            }
            // 解析 readme_analysis_json
            if (ra.getReadmeAnalysisJson() != null && !ra.getReadmeAnalysisJson().isEmpty()) {
                try {
                    Map<String, Object> rm = objectMapper.readValue(
                            ra.getReadmeAnalysisJson(), new TypeReference<Map<String, Object>>() {});
                    rav.setReadmeAnalysis(rm);
                } catch (Exception e) {
                    log.warn("Failed to parse readmeAnalysisJson for taskId={}: {}", taskId, e.getMessage());
                }
            }
            vo.setRepoAnalysis(rav);
        }
        // 报告数据
        ReportVO.ReportDataVO rdv = new ReportVO.ReportDataVO();
        rdv.setReproducibilityScore(report.getReproducibilityScore());
        rdv.setCompletenessScore(report.getCompletenessScore());
        rdv.setEnvironmentScore(report.getEnvironmentScore());
        rdv.setRiskLevel(report.getRiskLevel());
        rdv.setSummary(report.getSummary());
        rdv.setMethodSummary(report.getMethodSummary());
        rdv.setInnovationSummary(report.getInnovationSummary());
        rdv.setReproduceSteps(report.getReproduceSteps());
        rdv.setRiskTips(report.getRiskTips());
        rdv.setFinalAdvice(report.getFinalAdvice());
        vo.setReport(rdv);

        return vo;
    }

    @Override
    public ReportScoreVO getScores(Long taskId) {
        Report report = getReportByTaskId(taskId);
        ReportScoreVO vo = new ReportScoreVO();
        vo.setReproducibilityScore(report.getReproducibilityScore());
        vo.setCompletenessScore(report.getCompletenessScore());
        vo.setEnvironmentScore(report.getEnvironmentScore());
        vo.setRiskLevel(report.getRiskLevel());
        return vo;
    }

    @Override
    public void regenerateReport(Long taskId) {
        log.info("regenerateReport: taskId={}", taskId);

        // 获取已有数据
        PaperInfo pi = paperInfoMapper.selectOne(
                new LambdaQueryWrapper<PaperInfo>().eq(PaperInfo::getTaskId, taskId));
        RepoInfo ri = repoInfoMapper.selectOne(
                new LambdaQueryWrapper<RepoInfo>().eq(RepoInfo::getTaskId, taskId));
        RepoAnalysis ra = repoAnalysisMapper.selectOne(
                new LambdaQueryWrapper<RepoAnalysis>().eq(RepoAnalysis::getTaskId, taskId));

        if (pi == null && ri == null && ra == null) {
            throw new BusinessException("无可用数据，无法生成报告");
        }

        try {
            // 构建 paperInfo
            Map<String, Object> paperInfoMap = new HashMap<>();
            if (pi != null) {
                paperInfoMap.put("arxivId", pi.getArxivId());
                paperInfoMap.put("title", pi.getTitle());
                paperInfoMap.put("authors", pi.getAuthors());
                paperInfoMap.put("abstractText", pi.getAbstractText());
                paperInfoMap.put("publishedAt", pi.getPublishedAt());
                paperInfoMap.put("paperUrl", pi.getPaperUrl());
            }

            // 构建 repoInfo
            Map<String, Object> repoInfoMap = new HashMap<>();
            if (ri != null) {
                repoInfoMap.put("platform", ri.getPlatform());
                repoInfoMap.put("repoUrl", ri.getRepoUrl());
                repoInfoMap.put("repoName", ri.getRepoName());
                repoInfoMap.put("owner", ri.getOwner());
                repoInfoMap.put("stars", ri.getStars());
                repoInfoMap.put("forks", ri.getForks());
                repoInfoMap.put("defaultBranch", ri.getDefaultBranch());
                repoInfoMap.put("lastUpdatedAt", ri.getLastUpdatedAt());
                repoInfoMap.put("confidence", ri.getConfidence());
                repoInfoMap.put("confidenceReason", ri.getConfidenceReason());
            }

            // 构建 repoAnalysis
            Map<String, Object> repoAnalysisMap = new HashMap<>();
            if (ra != null) {
                repoAnalysisMap.put("hasReadme", ra.getHasReadme());
                repoAnalysisMap.put("hasRequirements", ra.getHasRequirements());
                repoAnalysisMap.put("hasEnvironmentYml", ra.getHasEnvironmentYml());
                repoAnalysisMap.put("hasDockerfile", ra.getHasDockerfile());
                repoAnalysisMap.put("hasLicense", ra.getHasLicense());
                repoAnalysisMap.put("hasTrainCode", ra.getHasTrainCode());
                repoAnalysisMap.put("hasInferenceCode", ra.getHasInferenceCode());
                repoAnalysisMap.put("hasDatasetDoc", ra.getHasDatasetDoc());
                repoAnalysisMap.put("hasWeightDoc", ra.getHasWeightDoc());
                repoAnalysisMap.put("readmeQualityScore", ra.getReadmeQualityScore());
                repoAnalysisMap.put("dependencyComplexityScore", ra.getDependencyComplexityScore());
                repoAnalysisMap.put("structureCompletenessScore", ra.getStructureCompletenessScore());
            }

            // 调用 AI service 生成报告
            GenerateReportRequest request = new GenerateReportRequest();
            request.setTaskId(taskId);
            request.setPaperInfo(paperInfoMap);
            request.setRepoInfo(repoInfoMap);
            request.setRepoAnalysis(repoAnalysisMap);

            AnalyzeResponse response = aiService.generateReportData(request);

            // 更新 report
            if (response.getReport() != null) {
                Report report = getReportByTaskId(taskId);
                AnalyzeResponse.ReportDTO rd = response.getReport();
                report.setReproducibilityScore(rd.getReproducibilityScore());
                report.setCompletenessScore(rd.getCompletenessScore());
                report.setEnvironmentScore(rd.getEnvironmentScore());
                report.setRiskLevel(rd.getRiskLevel());
                report.setSummary(rd.getSummary());
                report.setMethodSummary(rd.getMethodSummary());
                report.setInnovationSummary(rd.getInnovationSummary());
                report.setReproduceSteps(rd.getReproduceSteps());
                report.setRiskTips(rd.getRiskTips());
                report.setFinalAdvice(rd.getFinalAdvice());
                reportMapper.updateById(report);
            }

            log.info("regenerateReport: done, taskId={}", taskId);
        } catch (Exception e) {
            log.error("regenerateReport failed: taskId={}", taskId, e);
            throw new RuntimeException("报告重新生成失败", e);
        }
    }

    @Override
    public String exportMarkdown(Long taskId) {
        Report report = getReportByTaskId(taskId);
        ReportVO vo = buildReportVO(taskId, report);
        EnvironmentAnalysis env = getEnvironmentAnalysisSilently(taskId);
        List<DependencyAnalysis> deps = getDependenciesSilently(taskId);
        return MarkdownReportBuilder.build(vo, env, deps);
    }

    @Override
    public byte[] exportPdf(Long taskId) {
        // TODO: V2 实现 PDF 导出
        throw new UnsupportedOperationException("PDF 导出将在 V2 实现");
    }

    @Override
    public byte[] batchExportMarkdown(Long userId, List<Long> taskIds) {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        List<String> skipReasons = new ArrayList<>();

        try (ZipOutputStream zos = new ZipOutputStream(bos)) {
            for (Long taskId : taskIds) {
                // 校验任务归属
                PaperTask task = paperTaskMapper.selectById(taskId);
                if (task == null || !userId.equals(task.getUserId())) {
                    skipReasons.add(String.format("- 任务 %d: 任务不存在或无权限", taskId));
                    continue;
                }
                // 检查是否有报告
                Report report = reportMapper.selectOne(
                        new LambdaQueryWrapper<Report>().eq(Report::getTaskId, taskId));
                if (report == null) {
                    skipReasons.add(String.format("- 任务 %d: 报告尚未生成", taskId));
                    continue;
                }
                // 生成 Markdown
                ReportVO vo = buildReportVO(taskId, report);
                EnvironmentAnalysis env = getEnvironmentAnalysisSilently(taskId);
                List<DependencyAnalysis> deps = getDependenciesSilently(taskId);
                String markdown = MarkdownReportBuilder.build(vo, env, deps);
                byte[] bytes = markdown.getBytes(StandardCharsets.UTF_8);

                ZipEntry entry = new ZipEntry("repocheck-report-" + taskId + ".md");
                zos.putNextEntry(entry);
                zos.write(bytes);
                zos.closeEntry();
            }

            // 写入 summary.md 说明跳过原因
            if (!skipReasons.isEmpty()) {
                StringBuilder summary = new StringBuilder();
                summary.append("# 批量导出说明\n\n");
                summary.append("以下任务未成功导出报告：\n\n");
                for (String reason : skipReasons) {
                    summary.append(reason).append("\n");
                }
                byte[] summaryBytes = summary.toString().getBytes(StandardCharsets.UTF_8);

                ZipEntry summaryEntry = new ZipEntry("summary.md");
                zos.putNextEntry(summaryEntry);
                zos.write(summaryBytes);
                zos.closeEntry();
            }

            zos.finish();
        } catch (IOException e) {
            log.error("batchExportMarkdown failed", e);
            throw new RuntimeException("批量导出失败", e);
        }

        return bos.toByteArray();
    }

    private Report getReportByTaskId(Long taskId) {
        Report report = reportMapper.selectOne(new LambdaQueryWrapper<Report>().eq(Report::getTaskId, taskId));
        if (report == null) throw new BusinessException("报告不存在");
        return report;
    }

    /**
     * 静默查询环境分析 — 不存在返回 null，不抛异常
     */
    private EnvironmentAnalysis getEnvironmentAnalysisSilently(Long taskId) {
        try {
            return environmentAnalysisMapper.selectOne(
                    new LambdaQueryWrapper<EnvironmentAnalysis>().eq(EnvironmentAnalysis::getTaskId, taskId));
        } catch (Exception e) {
            log.warn("Failed to query environment_analysis for taskId={}: {}", taskId, e.getMessage());
            return null;
        }
    }

    /**
     * 静默查询依赖列表 — 不存在返回空列表，不抛异常
     */
    private List<DependencyAnalysis> getDependenciesSilently(Long taskId) {
        try {
            return dependencyAnalysisMapper.selectList(
                    new LambdaQueryWrapper<DependencyAnalysis>().eq(DependencyAnalysis::getTaskId, taskId));
        } catch (Exception e) {
            log.warn("Failed to query dependency_analysis for taskId={}: {}", taskId, e.getMessage());
            return Collections.emptyList();
        }
    }
}
