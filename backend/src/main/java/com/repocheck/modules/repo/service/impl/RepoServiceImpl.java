package com.repocheck.modules.repo.service.impl;

import com.repocheck.exception.BusinessException;
import com.repocheck.modules.repo.dto.UpdateRepoRequest;
import com.repocheck.modules.repo.entity.RepoCandidate;
import com.repocheck.modules.repo.entity.RepoInfo;
import com.repocheck.modules.repo.mapper.RepoCandidateMapper;
import com.repocheck.modules.repo.mapper.RepoInfoMapper;
import com.repocheck.modules.repo.service.RepoService;
import com.repocheck.modules.repo.vo.RepoCandidateVO;
import com.repocheck.modules.repo.vo.RepoInfoVO;
import com.repocheck.modules.task.entity.PaperTask;
import com.repocheck.modules.task.enums.TaskStatus;
import com.repocheck.modules.task.mapper.PaperTaskMapper;
import com.repocheck.modules.task.service.TaskTimelineService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Service
@RequiredArgsConstructor
public class RepoServiceImpl implements RepoService {

    private final RepoInfoMapper repoInfoMapper;
    private final RepoCandidateMapper repoCandidateMapper;
    private final PaperTaskMapper paperTaskMapper;
    private final TaskTimelineService taskTimelineService;

    private static final Pattern GITHUB_URL_PATTERN =
            Pattern.compile("https?://github\\.com/([^/]+)/([^/\\.]+)(?:\\.git)?(?:/.*)?");

    @Override
    public RepoInfoVO getRepoInfo(Long taskId) {
        RepoInfo ri = getRepoInfoOrNull(taskId);
        if (ri == null) throw new BusinessException("仓库信息不存在");
        return toVO(ri);
    }

    @Override
    public List<RepoCandidateVO> getCandidates(Long taskId) {
        List<RepoCandidate> candidates = repoCandidateMapper.selectList(
                new LambdaQueryWrapper<RepoCandidate>().eq(RepoCandidate::getTaskId, taskId));
        List<RepoCandidateVO> result = new ArrayList<>();
        for (RepoCandidate c : candidates) {
            result.add(toCandidateVO(c));
        }
        return result;
    }

    @Override
    @Transactional
    public void updateRepo(Long taskId, UpdateRepoRequest request) {
        // 1. 校验 taskId 存在
        PaperTask task = paperTaskMapper.selectById(taskId);
        if (task == null) {
            throw new BusinessException("任务不存在");
        }

        // 2. 校验并解析 GitHub URL
        String repoUrl = request.getRepoUrl().trim();
        Matcher matcher = GITHUB_URL_PATTERN.matcher(repoUrl);
        if (!matcher.matches()) {
            throw new BusinessException("请输入合法的 GitHub 仓库链接，例如 https://github.com/owner/repo");
        }
        String owner = matcher.group(1);
        String repoName = matcher.group(2);

        log.info("updateRepo: taskId={}, owner={}, repoName={}", taskId, owner, repoName);

        // 3. 写入或更新 repo_info
        RepoInfo ri = getRepoInfoOrNull(taskId);
        if (ri == null) {
            ri = new RepoInfo();
            ri.setTaskId(taskId);
        }
        ri.setPlatform("GitHub");
        ri.setRepoUrl(repoUrl);
        ri.setRepoName(repoName);
        ri.setOwner(owner);
        ri.setDefaultBranch("main");
        ri.setConfidence(BigDecimal.ONE);
        ri.setConfidenceReason("用户手动指定仓库");
        if (ri.getId() == null) {
            repoInfoMapper.insert(ri);
        } else {
            repoInfoMapper.updateById(ri);
        }

        // 4. 管理 repo_candidate
        // 4a. 先将该 taskId 下所有候选设为未选中
        List<RepoCandidate> existingCandidates = repoCandidateMapper.selectList(
                new LambdaQueryWrapper<RepoCandidate>().eq(RepoCandidate::getTaskId, taskId));
        for (RepoCandidate c : existingCandidates) {
            c.setSelected(0);
            repoCandidateMapper.updateById(c);
        }

        // 4b. 查找是否已有相同 owner/repoName 的候选
        RepoCandidate matched = null;
        for (RepoCandidate c : existingCandidates) {
            if (owner.equals(c.getOwner()) && repoName.equals(c.getRepoName())) {
                matched = c;
                break;
            }
        }

        if (matched != null) {
            matched.setRepoUrl(repoUrl);
            matched.setConfidence(BigDecimal.ONE);
            matched.setConfidenceReason("用户手动指定仓库");
            matched.setSource("manual");
            matched.setSelected(1);
            repoCandidateMapper.updateById(matched);
        } else {
            // 4c. 不存在则插入新候选
            RepoCandidate newCandidate = new RepoCandidate();
            newCandidate.setTaskId(taskId);
            newCandidate.setPlatform("GitHub");
            newCandidate.setRepoUrl(repoUrl);
            newCandidate.setRepoName(repoName);
            newCandidate.setOwner(owner);
            newCandidate.setDefaultBranch("main");
            newCandidate.setConfidence(BigDecimal.ONE);
            newCandidate.setConfidenceReason("用户手动指定仓库");
            newCandidate.setSource("manual");
            newCandidate.setSelected(1);
            repoCandidateMapper.insert(newCandidate);
        }

        // 5. 写入 task_timeline
        taskTimelineService.recordTimeline(taskId, TaskStatus.ANALYZING_REPO,
                "用户手动指定仓库，准备重新分析");

        log.info("updateRepo: done, taskId={}, repo={}/{}", taskId, owner, repoName);
    }

    @Override
    public void searchRepo(Long taskId) {
        // TODO: 触发重新搜索仓库，调用 AI 服务
        log.info("searchRepo requested for task={}", taskId);
    }

    private RepoInfo getRepoInfoOrNull(Long taskId) {
        return repoInfoMapper.selectOne(new LambdaQueryWrapper<RepoInfo>().eq(RepoInfo::getTaskId, taskId));
    }

    private RepoInfoVO toVO(RepoInfo ri) {
        RepoInfoVO vo = new RepoInfoVO();
        vo.setPlatform(ri.getPlatform()); vo.setRepoUrl(ri.getRepoUrl());
        vo.setRepoName(ri.getRepoName()); vo.setOwner(ri.getOwner());
        vo.setStars(ri.getStars()); vo.setForks(ri.getForks());
        vo.setDefaultBranch(ri.getDefaultBranch());
        vo.setLastUpdatedAt(ri.getLastUpdatedAt());
        vo.setConfidence(ri.getConfidence());
        vo.setConfidenceReason(ri.getConfidenceReason());
        return vo;
    }

    private RepoCandidateVO toCandidateVO(RepoCandidate c) {
        RepoCandidateVO vo = new RepoCandidateVO();
        vo.setPlatform(c.getPlatform()); vo.setRepoUrl(c.getRepoUrl());
        vo.setRepoName(c.getRepoName()); vo.setOwner(c.getOwner());
        vo.setStars(c.getStars()); vo.setForks(c.getForks());
        vo.setDefaultBranch(c.getDefaultBranch());
        vo.setLastUpdatedAt(c.getLastUpdatedAt());
        vo.setConfidence(c.getConfidence());
        vo.setConfidenceReason(c.getConfidenceReason());
        return vo;
    }
}
