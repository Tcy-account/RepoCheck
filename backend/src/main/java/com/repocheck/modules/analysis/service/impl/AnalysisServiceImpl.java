package com.repocheck.modules.analysis.service.impl;

import com.repocheck.exception.BusinessException;
import com.repocheck.modules.ai.dto.AnalyzeResponse;
import com.repocheck.modules.ai.dto.AnalyzeStructureRequest;
import com.repocheck.modules.ai.service.AiService;
import com.repocheck.modules.analysis.entity.RepoAnalysis;
import com.repocheck.modules.analysis.mapper.RepoAnalysisMapper;
import com.repocheck.modules.analysis.service.AnalysisService;
import com.repocheck.modules.analysis.vo.ReadmeAnalysisVO;
import com.repocheck.modules.analysis.vo.RepoAnalysisVO;
import com.repocheck.modules.paper.entity.PaperInfo;
import com.repocheck.modules.paper.mapper.PaperInfoMapper;
import com.repocheck.modules.repo.entity.RepoInfo;
import com.repocheck.modules.repo.mapper.RepoInfoMapper;
import com.repocheck.modules.task.enums.TaskStatus;
import com.repocheck.modules.task.service.TaskTimelineService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class AnalysisServiceImpl implements AnalysisService {

    private final RepoAnalysisMapper repoAnalysisMapper;
    private final PaperInfoMapper paperInfoMapper;
    private final RepoInfoMapper repoInfoMapper;
    private final AiService aiService;
    private final TaskTimelineService taskTimelineService;
    private final ObjectMapper objectMapper;

    @Override
    public RepoAnalysisVO getAnalysis(Long taskId) {
        RepoAnalysis ra = getAnalysisByTaskId(taskId);
        return toVO(ra);
    }

    @Override
    public void rebuildAnalysis(Long taskId) {
        log.info("rebuildAnalysis: taskId={}", taskId);

        // 1. 校验 repo_info 存在
        RepoInfo ri = repoInfoMapper.selectOne(
                new LambdaQueryWrapper<RepoInfo>().eq(RepoInfo::getTaskId, taskId));
        if (ri == null) {
            throw new BusinessException("仓库信息不存在，请先手动指定仓库");
        }

        // 2. 获取论文信息
        PaperInfo pi = paperInfoMapper.selectOne(
                new LambdaQueryWrapper<PaperInfo>().eq(PaperInfo::getTaskId, taskId));

        // 3. 设置状态为 ANALYZING_REPO
        taskTimelineService.updateTaskStatus(taskId, TaskStatus.ANALYZING_REPO,
                "用户手动指定仓库，正在重新分析");

        try {
            // 4. 构建请求
            AnalyzeStructureRequest.PaperInfoDTO paperInfoDTO = null;
            if (pi != null) {
                paperInfoDTO = new AnalyzeStructureRequest.PaperInfoDTO();
                paperInfoDTO.setArxivId(pi.getArxivId());
                paperInfoDTO.setTitle(pi.getTitle());
                paperInfoDTO.setAbstractText(pi.getAbstractText());
            }

            AnalyzeStructureRequest.RepoInfoDTO repoInfoDTO = new AnalyzeStructureRequest.RepoInfoDTO();
            repoInfoDTO.setPlatform(ri.getPlatform());
            repoInfoDTO.setRepoUrl(ri.getRepoUrl());
            repoInfoDTO.setRepoName(ri.getRepoName());
            repoInfoDTO.setOwner(ri.getOwner());
            repoInfoDTO.setStars(ri.getStars());
            repoInfoDTO.setForks(ri.getForks());
            repoInfoDTO.setDefaultBranch(ri.getDefaultBranch());

            AnalyzeStructureRequest request = new AnalyzeStructureRequest();
            request.setTaskId(taskId);
            request.setRepoInfo(repoInfoDTO);
            request.setPaperInfo(paperInfoDTO);

            // 5. 调用 AI service
            AnalyzeResponse response = aiService.analyzeStructure(request);

            // 6. 写入生成报告时间线
            taskTimelineService.recordTimeline(taskId, TaskStatus.GENERATING_REPORT,
                    "正在基于指定仓库重新生成报告");

            // 7. 覆盖旧结果
            aiService.saveOrUpdateResults(taskId, response);

            // 8. 更新状态为 SUCCESS
            taskTimelineService.updateTaskStatus(taskId, TaskStatus.SUCCESS,
                    "指定仓库分析完成");

            log.info("rebuildAnalysis: done, taskId={}", taskId);
        } catch (Exception e) {
            log.error("rebuildAnalysis failed: taskId={}", taskId, e);
            taskTimelineService.updateTaskStatus(taskId, TaskStatus.FAILED,
                    "指定仓库分析失败：" + e.getMessage());
            throw new RuntimeException("重新分析失败", e);
        }
    }

    @Override
    public List<String> getFileList(Long taskId) {
        RepoAnalysis ra = getAnalysisByTaskId(taskId);
        List<String> files = new ArrayList<>();
        if (Boolean.TRUE.equals(ra.getHasReadme())) files.add("README.md");
        if (Boolean.TRUE.equals(ra.getHasRequirements())) files.add("requirements.txt");
        if (Boolean.TRUE.equals(ra.getHasDockerfile())) files.add("Dockerfile");
        if (Boolean.TRUE.equals(ra.getHasLicense())) files.add("LICENSE");
        if (Boolean.TRUE.equals(ra.getHasTrainCode())) files.add("train.py");
        if (Boolean.TRUE.equals(ra.getHasInferenceCode())) files.add("infer.py");
        return files;
    }

    @Override
    public ReadmeAnalysisVO getReadmeAnalysis(Long taskId) {
        RepoAnalysis ra = getAnalysisByTaskId(taskId);
        ReadmeAnalysisVO vo = new ReadmeAnalysisVO();

        if (ra.getReadmeAnalysisJson() != null && !ra.getReadmeAnalysisJson().isEmpty()) {
            try {
                Map<String, Object> map = objectMapper.readValue(
                        ra.getReadmeAnalysisJson(), new TypeReference<Map<String, Object>>() {});
                vo.setHasInstallSection(toBool(map.get("hasInstallSection")));
                vo.setHasTrainSection(toBool(map.get("hasTrainSection")));
                vo.setHasInferenceSection(toBool(map.get("hasInferenceSection")));
                vo.setHasDatasetSection(toBool(map.get("hasDatasetSection")));
                vo.setHasWeightSection(toBool(map.get("hasWeightSection")));
                vo.setHasCitationSection(toBool(map.get("hasCitationSection")));
                vo.setHasExampleCommands(toBool(map.get("hasExampleCommands")));
                if (map.get("readmeLength") != null) {
                    vo.setReadmeLength(((Number) map.get("readmeLength")).intValue());
                }
            } catch (Exception e) {
                log.warn("Failed to parse readmeAnalysisJson for taskId={}: {}", taskId, e.getMessage());
            }
        }
        vo.setReadmeQualityScore(ra.getReadmeQualityScore());
        return vo;
    }

    private static Boolean toBool(Object v) {
        return v instanceof Boolean ? (Boolean) v : null;
    }

    private RepoAnalysis getAnalysisByTaskId(Long taskId) {
        RepoAnalysis ra = repoAnalysisMapper.selectOne(
                new LambdaQueryWrapper<RepoAnalysis>().eq(RepoAnalysis::getTaskId, taskId));
        if (ra == null) throw new BusinessException("分析结果不存在");
        return ra;
    }

    private RepoAnalysisVO toVO(RepoAnalysis ra) {
        RepoAnalysisVO vo = new RepoAnalysisVO();
        vo.setHasReadme(ra.getHasReadme()); vo.setHasRequirements(ra.getHasRequirements());
        vo.setHasEnvironmentYml(ra.getHasEnvironmentYml()); vo.setHasDockerfile(ra.getHasDockerfile());
        vo.setHasLicense(ra.getHasLicense()); vo.setHasTrainCode(ra.getHasTrainCode());
        vo.setHasInferenceCode(ra.getHasInferenceCode()); vo.setHasDatasetDoc(ra.getHasDatasetDoc());
        vo.setHasWeightDoc(ra.getHasWeightDoc());
        vo.setReadmeQualityScore(ra.getReadmeQualityScore());
        vo.setDependencyComplexityScore(ra.getDependencyComplexityScore());
        vo.setStructureCompletenessScore(ra.getStructureCompletenessScore());
        // 解析 file_matches_json
        if (ra.getFileMatchesJson() != null && !ra.getFileMatchesJson().isEmpty()) {
            try {
                Map<String, List<String>> fm = objectMapper.readValue(
                        ra.getFileMatchesJson(), new TypeReference<Map<String, List<String>>>() {});
                vo.setFileMatches(fm);
            } catch (Exception e) {
                log.warn("Failed to parse fileMatchesJson for taskId={}: {}", ra.getTaskId(), e.getMessage());
            }
        }
        // 解析 readme_analysis_json
        if (ra.getReadmeAnalysisJson() != null && !ra.getReadmeAnalysisJson().isEmpty()) {
            try {
                Map<String, Object> rm = objectMapper.readValue(
                        ra.getReadmeAnalysisJson(), new TypeReference<Map<String, Object>>() {});
                vo.setReadmeAnalysis(rm);
            } catch (Exception e) {
                log.warn("Failed to parse readmeAnalysisJson for taskId={}: {}", ra.getTaskId(), e.getMessage());
            }
        }
        return vo;
    }
}
