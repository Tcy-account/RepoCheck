package com.repocheck.modules.ai.service.impl;

import com.repocheck.common.ErrorCode;
import com.repocheck.exception.BusinessException;
import com.repocheck.modules.ai.dto.AnalyzeEnvironmentRequest;
import com.repocheck.modules.ai.dto.AnalyzeEnvironmentResponse;
import com.repocheck.modules.ai.dto.AnalyzeRequest;
import com.repocheck.modules.ai.dto.AnalyzeResponse;
import com.repocheck.modules.ai.dto.AnalyzeStructureRequest;
import com.repocheck.modules.ai.dto.GenerateReportRequest;
import com.repocheck.modules.ai.service.AiService;
import com.repocheck.modules.analysis.entity.RepoAnalysis;
import com.repocheck.modules.analysis.mapper.RepoAnalysisMapper;
import com.repocheck.modules.paper.entity.PaperInfo;
import com.repocheck.modules.paper.mapper.PaperInfoMapper;
import com.repocheck.modules.repo.entity.RepoInfo;
import com.repocheck.modules.repo.mapper.RepoInfoMapper;
import com.repocheck.modules.report.entity.Report;
import com.repocheck.modules.report.mapper.ReportMapper;
import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.enums.TaskStatus;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import com.repocheck.modules.task.service.TaskTimelineService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiServiceImpl implements AiService {

    private final RestTemplate restTemplate;
    private final PaperTaskMapper paperTaskMapper;
    private final PaperInfoMapper paperInfoMapper;
    private final RepoInfoMapper repoInfoMapper;
    private final RepoAnalysisMapper repoAnalysisMapper;
    private final ReportMapper reportMapper;
    private final TaskTimelineService taskTimelineService;
    private final ObjectMapper objectMapper;

    @Value("${ai-service.base-url}")
    private String aiServiceBaseUrl;

    /**
     * 分析任务入口（带事务）
     *
     * 整个 saveResults + SUCCESS 状态更新在一个事务内完成。
     * PARSING_PAPER 和 FAILED 状态通过 TaskTimelineService 写入，
     * 它们是不同的 Bean，拥有独立事务，不会被当前事务的异常回滚。
     */
    @Override
    @Transactional
    public void analyzeTask(Long taskId, String paperUrl) {
        // 写入 PARSING_PAPER（独立事务，通过 TaskTimelineService）
        taskTimelineService.updateTaskStatus(taskId, TaskStatus.PARSING_PAPER, null);

        // TODO V2: 将 AI service 拆分为多个阶段调用，以便写入 SEARCHING_REPO / ANALYZING_REPO / GENERATING_REPORT 状态。
        //   V1 中整个分析流程发生在一次 HTTP 调用内，中间态对后端不可见。

        // 1. 调用 AI 服务
        AnalyzeResponse response;
        try {
            response = callAiAnalyze(taskId, paperUrl);
        } catch (Exception e) {
            log.error("Task {} AI call failed", taskId, e);
            // 优先使用 BusinessException 中的用户可读消息
            String msg = (e instanceof BusinessException)
                    ? e.getMessage()
                    : "AI 服务暂时不可用，请确认 ai-service 已启动";
            taskTimelineService.updateTaskStatus(taskId, TaskStatus.FAILED, "分析失败：" + msg);
            return;
        }

        // 2. 校验关键数据
        if (response.getPaperInfo() == null
                || response.getPaperInfo().getTitle() == null
                || response.getPaperInfo().getTitle().isBlank()) {
            log.error("Task {} AI returned incomplete data (no paperTitle)", taskId);
            taskTimelineService.updateTaskStatus(taskId, TaskStatus.FAILED,
                    "分析失败：AI 服务返回数据不完整，论文标题缺失");
            return;
        }

        // 3. 取消防覆盖：检查任务是否已被取消
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task != null && TaskStatus.CANCELLED.name().equals(task.getStatus())) {
            log.info("Task {} has been cancelled, discarding AI results", taskId);
            return;
        }

        // 4. 幂等保存结果（在当前事务中）
        try {
            doSaveResults(taskId, response);
        } catch (Exception e) {
            log.error("Task {} failed to persist results", taskId, e);
            taskTimelineService.updateTaskStatus(taskId, TaskStatus.FAILED,
                    "保存结果失败：系统异常，请查看后端日志");
            return;
        }

        // 5. 标记 SUCCESS（独立事务）
        taskTimelineService.updateTaskStatus(taskId, TaskStatus.SUCCESS, null);
        log.info("Task {} analysis completed successfully", taskId);
    }

    @Override
    public AnalyzeResponse analyzeStructure(AnalyzeStructureRequest request) {
        String url = aiServiceBaseUrl + "/api/repo/analyze-structure";
        log.info("Calling AI analyze-structure: {} with taskId={}", url, request.getTaskId());
        try {
            AnalyzeResponse response = restTemplate.postForObject(url, request, AnalyzeResponse.class);
            if (response == null) {
                throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                        "AI 服务 analyze-structure 返回空响应");
            }
            return response;
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("AI analyze-structure failed for taskId={}: {}", request.getTaskId(), e.getMessage());
            throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                    "AI 服务调用失败：" + e.getMessage(), e);
        }
    }

    @Override
    public AnalyzeResponse generateReportData(GenerateReportRequest request) {
        String url = aiServiceBaseUrl + "/api/report/generate";
        log.info("Calling AI report/generate: {} with taskId={}", url, request.getTaskId());
        try {
            AnalyzeResponse response = restTemplate.postForObject(url, request, AnalyzeResponse.class);
            if (response == null) {
                throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                        "AI 服务 report/generate 返回空响应");
            }
            return response;
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("AI report/generate failed for taskId={}: {}", request.getTaskId(), e.getMessage());
            throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                    "AI 服务调用失败：" + e.getMessage(), e);
        }
    }

    @Override
    public AnalyzeEnvironmentResponse analyzeEnvironment(AnalyzeEnvironmentRequest request) {
        String url = aiServiceBaseUrl + "/api/environment/analyze";
        log.info("Calling AI environment/analyze: {} with taskId={}", url, request.getTaskId());
        try {
            AnalyzeEnvironmentResponse response = restTemplate.postForObject(
                    url, request, AnalyzeEnvironmentResponse.class);
            if (response == null) {
                throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                        "AI 服务 environment/analyze 返回空响应");
            }
            return response;
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("AI environment/analyze failed for taskId={}: {}", request.getTaskId(), e.getMessage());
            throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                    "AI 服务调用失败：" + e.getMessage(), e);
        }
    }

    // ═══════════════════════════════════════════════════════════
    // 私有辅助方法
    // ═══════════════════════════════════════════════════════════

    /**
     * 调用 AI /api/analyze 接口，区分超时/连接异常
     */
    private AnalyzeResponse callAiAnalyze(Long taskId, String paperUrl) {
        String url = aiServiceBaseUrl + "/api/analyze";
        AnalyzeRequest request = new AnalyzeRequest(taskId, paperUrl);
        log.info("Calling AI service: {} with taskId={}", url, taskId);

        try {
            AnalyzeResponse response = restTemplate.postForObject(url, request, AnalyzeResponse.class);
            if (response == null) {
                throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                        "AI 服务返回空响应，请稍后重试");
            }
            return response;
        } catch (ResourceAccessException e) {
            Throwable cause = e.getCause();
            if (cause instanceof SocketTimeoutException) {
                throw new BusinessException(ErrorCode.AI_SERVICE_TIMEOUT,
                        "AI 服务调用超时，请稍后重试", e);
            }
            if (cause instanceof ConnectException) {
                throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                        "AI 服务暂时不可用，请确认 ai-service 已启动", e);
            }
            throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                    "AI 服务调用失败：" + e.getMessage(), e);
        } catch (BusinessException e) {
            throw e; // 原样抛出
        } catch (Exception e) {
            throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                    "AI 服务调用失败：" + e.getMessage(), e);
        }
    }

    /**
     * 幂等保存分析结果。
     *
     * paper_info / repo_info / repo_analysis / report 四张表：
     *   - 如果 task_id 已存在 → update
     *   - 如果 task_id 不存在 → insert
     */
    private void doSaveResults(Long taskId, AnalyzeResponse response) {
        // 更新 paper_task 标题
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task != null && response.getPaperInfo() != null) {
            task.setPaperTitle(response.getPaperInfo().getTitle());
            paperTaskMapper.updateById(task);
        }

        // paper_info
        if (response.getPaperInfo() != null) {
            PaperInfo pi = mapPaperInfo(taskId, response.getPaperInfo());
            upsertPaperInfo(taskId, pi);
        }

        // repo_info
        if (response.getRepoInfo() != null) {
            RepoInfo ri = mapRepoInfo(taskId, response.getRepoInfo());
            upsertRepoInfo(taskId, ri);
        }

        // repo_analysis
        if (response.getRepoAnalysis() != null) {
            RepoAnalysis ra = mapRepoAnalysis(taskId, response.getRepoAnalysis());
            upsertRepoAnalysis(taskId, ra);
        }

        // report
        if (response.getReport() != null) {
            Report r = mapReport(taskId, response.getReport());
            upsertReport(taskId, r);
        }
    }

    // ── upsert 方法 ──

    private void upsertPaperInfo(Long taskId, PaperInfo entity) {
        PaperInfo existing = paperInfoMapper.selectOne(
                new LambdaQueryWrapper<PaperInfo>().eq(PaperInfo::getTaskId, taskId));
        if (existing != null) {
            entity.setId(existing.getId());
            paperInfoMapper.updateById(entity);
        } else {
            paperInfoMapper.insert(entity);
        }
    }

    private void upsertRepoInfo(Long taskId, RepoInfo entity) {
        RepoInfo existing = repoInfoMapper.selectOne(
                new LambdaQueryWrapper<RepoInfo>().eq(RepoInfo::getTaskId, taskId));
        if (existing != null) {
            entity.setId(existing.getId());
            repoInfoMapper.updateById(entity);
        } else {
            repoInfoMapper.insert(entity);
        }
    }

    private void upsertRepoAnalysis(Long taskId, RepoAnalysis entity) {
        RepoAnalysis existing = repoAnalysisMapper.selectOne(
                new LambdaQueryWrapper<RepoAnalysis>().eq(RepoAnalysis::getTaskId, taskId));
        if (existing != null) {
            entity.setId(existing.getId());
            repoAnalysisMapper.updateById(entity);
        } else {
            repoAnalysisMapper.insert(entity);
        }
    }

    private void upsertReport(Long taskId, Report entity) {
        Report existing = reportMapper.selectOne(
                new LambdaQueryWrapper<Report>().eq(Report::getTaskId, taskId));
        if (existing != null) {
            entity.setId(existing.getId());
            reportMapper.updateById(entity);
        } else {
            reportMapper.insert(entity);
        }
    }

    // ── DTO → Entity 映射 ──

    private PaperInfo mapPaperInfo(Long taskId, AnalyzeResponse.PaperInfoDTO dto) {
        PaperInfo pi = new PaperInfo();
        pi.setTaskId(taskId);
        pi.setArxivId(dto.getArxivId());
        pi.setTitle(dto.getTitle());
        pi.setAuthors(dto.getAuthors());
        pi.setAbstractText(dto.getAbstractText());
        pi.setPublishedAt(dto.getPublishedAt());
        pi.setPaperUrl(dto.getPaperUrl());
        return pi;
    }

    private RepoInfo mapRepoInfo(Long taskId, AnalyzeResponse.RepoInfoDTO dto) {
        RepoInfo ri = new RepoInfo();
        ri.setTaskId(taskId);
        ri.setPlatform(dto.getPlatform());
        ri.setRepoUrl(dto.getRepoUrl());
        ri.setRepoName(dto.getRepoName());
        ri.setOwner(dto.getOwner());
        ri.setStars(dto.getStars());
        ri.setForks(dto.getForks());
        ri.setDefaultBranch(dto.getDefaultBranch());
        ri.setLastUpdatedAt(dto.getLastUpdatedAt());
        ri.setConfidence(dto.getConfidence());
        ri.setConfidenceReason(dto.getConfidenceReason());
        return ri;
    }

    private RepoAnalysis mapRepoAnalysis(Long taskId, AnalyzeResponse.RepoAnalysisDTO dto) {
        RepoAnalysis ra = new RepoAnalysis();
        ra.setTaskId(taskId);
        ra.setHasReadme(dto.getHasReadme());
        ra.setHasRequirements(dto.getHasRequirements());
        ra.setHasEnvironmentYml(dto.getHasEnvironmentYml());
        ra.setHasDockerfile(dto.getHasDockerfile());
        ra.setHasLicense(dto.getHasLicense());
        ra.setHasTrainCode(dto.getHasTrainCode());
        ra.setHasInferenceCode(dto.getHasInferenceCode());
        ra.setHasDatasetDoc(dto.getHasDatasetDoc());
        ra.setHasWeightDoc(dto.getHasWeightDoc());
        ra.setReadmeQualityScore(dto.getReadmeQualityScore());
        ra.setDependencyComplexityScore(dto.getDependencyComplexityScore());
        ra.setStructureCompletenessScore(dto.getStructureCompletenessScore());
        // 序列化 fileMatches 为 JSON 存入数据库
        Map<String, Object> fm = dto.getFileMatches();
        if (fm != null && !fm.isEmpty()) {
            try {
                ra.setFileMatchesJson(objectMapper.writeValueAsString(fm));
            } catch (Exception e) {
                log.warn("Failed to serialize fileMatches for taskId={}: {}", taskId, e.getMessage());
            }
        }
        // 序列化 readmeAnalysis 为 JSON 存入数据库
        Map<String, Object> raMap = dto.getReadmeAnalysis();
        if (raMap != null && !raMap.isEmpty()) {
            try {
                ra.setReadmeAnalysisJson(objectMapper.writeValueAsString(raMap));
            } catch (Exception e) {
                log.warn("Failed to serialize readmeAnalysis for taskId={}: {}", taskId, e.getMessage());
            }
        }
        return ra;
    }

    private Report mapReport(Long taskId, AnalyzeResponse.ReportDTO dto) {
        Report r = new Report();
        r.setTaskId(taskId);
        r.setReproducibilityScore(dto.getReproducibilityScore());
        r.setCompletenessScore(dto.getCompletenessScore());
        r.setEnvironmentScore(dto.getEnvironmentScore());
        r.setRiskLevel(dto.getRiskLevel());
        r.setSummary(dto.getSummary());
        r.setMethodSummary(dto.getMethodSummary());
        r.setInnovationSummary(dto.getInnovationSummary());
        r.setReproduceSteps(dto.getReproduceSteps());
        r.setRiskTips(dto.getRiskTips());
        r.setFinalAdvice(dto.getFinalAdvice());
        return r;
    }

    // ═══════════════════════════════════════════════════════════
    // 手动指定仓库重新分析
    // ═══════════════════════════════════════════════════════════

    /**
     * 保存或覆盖结果（用于重新分析场景）
     *
     * 同样使用幂等 upsert。与 doSaveResults 的区别：
     *   - 不更新 paper_task.paperTitle（已在最初设置）
     *   - 调用方（AnalysisServiceImpl）自己写状态和 timeline
     */
    @Override
    public void saveOrUpdateResults(Long taskId, AnalyzeResponse response) {
        // 取消防覆盖
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task != null && TaskStatus.CANCELLED.name().equals(task.getStatus())) {
            log.info("Task {} has been cancelled, discarding rebuild results", taskId);
            return;
        }

        // repo_info 幂等 upsert
        if (response.getRepoInfo() != null) {
            RepoInfo ri = mapRepoInfo(taskId, response.getRepoInfo());
            upsertRepoInfo(taskId, ri);
        }

        // repo_analysis 幂等 upsert
        if (response.getRepoAnalysis() != null) {
            RepoAnalysis ra = mapRepoAnalysis(taskId, response.getRepoAnalysis());
            upsertRepoAnalysis(taskId, ra);
        }

        // report 幂等 upsert
        if (response.getReport() != null) {
            Report r = mapReport(taskId, response.getReport());
            upsertReport(taskId, r);
        }
    }

    @Override
    public void recordTimeline(Long taskId, TaskStatus status, String message) {
        taskTimelineService.recordTimeline(taskId, status, message);
    }

    @Override
    public void updateStatus(Long taskId, TaskStatus status, String errorMessage) {
        taskTimelineService.updateTaskStatus(taskId, status, errorMessage);
    }
}
