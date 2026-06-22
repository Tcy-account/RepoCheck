package com.repocheck.modules.environment.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.repocheck.common.ErrorCode;
import com.repocheck.exception.BusinessException;
import com.repocheck.modules.ai.dto.AnalyzeEnvironmentRequest;
import com.repocheck.modules.ai.dto.AnalyzeEnvironmentResponse;
import com.repocheck.modules.ai.service.AiService;
import com.repocheck.modules.environment.entity.DependencyAnalysis;
import com.repocheck.modules.environment.entity.EnvironmentAnalysis;
import com.repocheck.modules.environment.mapper.DependencyAnalysisMapper;
import com.repocheck.modules.environment.mapper.EnvironmentAnalysisMapper;
import com.repocheck.modules.environment.service.EnvironmentService;
import com.repocheck.modules.environment.vo.DependencyAnalysisVO;
import com.repocheck.modules.environment.vo.EnvironmentAnalysisVO;
import com.repocheck.modules.environment.vo.EnvironmentReportVO;
import com.repocheck.modules.repo.entity.RepoInfo;
import com.repocheck.modules.repo.mapper.RepoInfoMapper;
import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class EnvironmentServiceImpl implements EnvironmentService {

    private final AiService aiService;
    private final PaperTaskMapper paperTaskMapper;
    private final RepoInfoMapper repoInfoMapper;
    private final EnvironmentAnalysisMapper environmentAnalysisMapper;
    private final DependencyAnalysisMapper dependencyAnalysisMapper;

    @Override
    public EnvironmentAnalysisVO getEnvironmentAnalysis(Long taskId) {
        EnvironmentAnalysis entity = environmentAnalysisMapper.selectOne(
                new LambdaQueryWrapper<EnvironmentAnalysis>().eq(EnvironmentAnalysis::getTaskId, taskId));
        if (entity == null) {
            throw new BusinessException(ErrorCode.REPORT_NOT_FOUND, "环境分析尚未生成");
        }
        return toVO(entity);
    }

    @Override
    public List<DependencyAnalysisVO> getDependencies(Long taskId) {
        List<DependencyAnalysis> entities = dependencyAnalysisMapper.selectList(
                new LambdaQueryWrapper<DependencyAnalysis>().eq(DependencyAnalysis::getTaskId, taskId));
        if (entities.isEmpty()) {
            // 不报错，返回空列表供前端展示
            return Collections.emptyList();
        }
        return entities.stream().map(this::toVO).collect(Collectors.toList());
    }

    @Override
    @Transactional
    public EnvironmentReportVO rebuildAnalysis(Long userId, Long taskId) {
        // 1. 校验任务存在且属于当前用户
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task == null) {
            throw new BusinessException(ErrorCode.TASK_NOT_FOUND);
        }
        if (!userId.equals(task.getUserId())) {
            throw new BusinessException(ErrorCode.FORBIDDEN);
        }

        // 2. 校验 repo_info 存在
        RepoInfo repoInfo = repoInfoMapper.selectOne(
                new LambdaQueryWrapper<RepoInfo>().eq(RepoInfo::getTaskId, taskId));
        if (repoInfo == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "仓库信息不存在，请先完成基础分析");
        }

        // 3. 调用 ai-service
        AnalyzeEnvironmentRequest req = new AnalyzeEnvironmentRequest();
        req.setTaskId(taskId);
        AnalyzeEnvironmentRequest.RepoInfoDTO ri = new AnalyzeEnvironmentRequest.RepoInfoDTO();
        ri.setPlatform(repoInfo.getPlatform());
        ri.setRepoUrl(repoInfo.getRepoUrl());
        ri.setRepoName(repoInfo.getRepoName());
        ri.setOwner(repoInfo.getOwner());
        ri.setDefaultBranch(repoInfo.getDefaultBranch());
        req.setRepoInfo(ri);

        log.info("Calling AI environment/analyze for taskId={}, repo={}/{}",
                taskId, repoInfo.getOwner(), repoInfo.getRepoName());

        AnalyzeEnvironmentResponse response;
        try {
            response = aiService.analyzeEnvironment(req);
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("Environment analysis failed for taskId={}", taskId, e);
            throw new BusinessException(ErrorCode.AI_SERVICE_ERROR,
                    "环境分析失败：" + e.getMessage(), e);
        }

        // 4. 删除旧依赖记录
        dependencyAnalysisMapper.delete(
                new LambdaQueryWrapper<DependencyAnalysis>().eq(DependencyAnalysis::getTaskId, taskId));

        // 5. 插入新依赖
        if (response.getDependencies() != null) {
            for (AnalyzeEnvironmentResponse.DependencyDTO dto : response.getDependencies()) {
                DependencyAnalysis da = new DependencyAnalysis();
                da.setTaskId(taskId);
                da.setFileType(dto.getFileType());
                da.setFilePath(dto.getFilePath());
                da.setPackageName(dto.getPackageName());
                da.setVersionSpec(dto.getVersionSpec());
                da.setSource(dto.getSource());
                da.setRiskLevel(dto.getRiskLevel());
                da.setRiskReason(dto.getRiskReason());
                dependencyAnalysisMapper.insert(da);
            }
        }

        // 6. environment_analysis upsert
        if (response.getEnvironmentAnalysis() != null) {
            AnalyzeEnvironmentResponse.EnvironmentDTO eaDTO = response.getEnvironmentAnalysis();
            EnvironmentAnalysis ea = new EnvironmentAnalysis();
            ea.setTaskId(taskId);
            ea.setPythonVersion(eaDTO.getPythonVersion());
            ea.setCudaVersion(eaDTO.getCudaVersion());
            ea.setMainFramework(eaDTO.getMainFramework());
            ea.setFrameworkVersion(eaDTO.getFrameworkVersion());
            ea.setRequiresGpu(eaDTO.getRequiresGpu() != null && eaDTO.getRequiresGpu() ? 1 : 0);
            ea.setHasDocker(eaDTO.getHasDocker() != null && eaDTO.getHasDocker() ? 1 : 0);
            ea.setDockerBaseImage(eaDTO.getDockerBaseImage());
            ea.setDependencyRiskScore(eaDTO.getDependencyRiskScore());
            ea.setCudaRiskScore(eaDTO.getCudaRiskScore());
            ea.setDockerReadinessScore(eaDTO.getDockerReadinessScore());
            ea.setEnvironmentScore(eaDTO.getEnvironmentScore());
            ea.setRiskLevel(eaDTO.getRiskLevel());
            ea.setRiskSummary(eaDTO.getRiskSummary());
            ea.setInstallAdvice(eaDTO.getInstallAdvice());

            EnvironmentAnalysis existing = environmentAnalysisMapper.selectOne(
                    new LambdaQueryWrapper<EnvironmentAnalysis>().eq(EnvironmentAnalysis::getTaskId, taskId));
            if (existing != null) {
                ea.setId(existing.getId());
                environmentAnalysisMapper.updateById(ea);
            } else {
                environmentAnalysisMapper.insert(ea);
            }
        }

        // 7. 返回
        log.info("Environment analysis completed for taskId={}", taskId);
        return buildReport(taskId);
    }

    // ── VO 组装 ──

    private EnvironmentReportVO buildReport(Long taskId) {
        EnvironmentReportVO report = new EnvironmentReportVO();
        report.setTaskId(taskId);
        report.setEnvironmentAnalysis(getEnvironmentAnalysis(taskId));
        report.setDependencies(getDependencies(taskId));
        return report;
    }

    private EnvironmentAnalysisVO toVO(EnvironmentAnalysis ea) {
        EnvironmentAnalysisVO vo = new EnvironmentAnalysisVO();
        vo.setTaskId(ea.getTaskId());
        vo.setPythonVersion(ea.getPythonVersion());
        vo.setCudaVersion(ea.getCudaVersion());
        vo.setMainFramework(ea.getMainFramework());
        vo.setFrameworkVersion(ea.getFrameworkVersion());
        vo.setRequiresGpu(ea.getRequiresGpu() != null && ea.getRequiresGpu() == 1);
        vo.setHasDocker(ea.getHasDocker() != null && ea.getHasDocker() == 1);
        vo.setDockerBaseImage(ea.getDockerBaseImage());
        vo.setDependencyRiskScore(ea.getDependencyRiskScore());
        vo.setCudaRiskScore(ea.getCudaRiskScore());
        vo.setDockerReadinessScore(ea.getDockerReadinessScore());
        vo.setEnvironmentScore(ea.getEnvironmentScore());
        vo.setRiskLevel(ea.getRiskLevel());
        vo.setRiskSummary(ea.getRiskSummary());
        vo.setInstallAdvice(ea.getInstallAdvice());
        return vo;
    }

    private DependencyAnalysisVO toVO(DependencyAnalysis da) {
        DependencyAnalysisVO vo = new DependencyAnalysisVO();
        vo.setId(da.getId());
        vo.setTaskId(da.getTaskId());
        vo.setFileType(da.getFileType());
        vo.setFilePath(da.getFilePath());
        vo.setPackageName(da.getPackageName());
        vo.setVersionSpec(da.getVersionSpec());
        vo.setSource(da.getSource());
        vo.setRiskLevel(da.getRiskLevel());
        vo.setRiskReason(da.getRiskReason());
        return vo;
    }
}
