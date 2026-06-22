package com.repocheck.modules.paper.service.impl;

import com.repocheck.exception.BusinessException;
import com.repocheck.modules.paper.entity.PaperInfo;
import com.repocheck.modules.paper.mapper.PaperInfoMapper;
import com.repocheck.modules.paper.service.PaperService;
import com.repocheck.modules.paper.vo.PaperInfoVO;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class PaperServiceImpl implements PaperService {

    private final PaperInfoMapper paperInfoMapper;

    @Override
    public PaperInfoVO getPaperInfo(Long taskId) {
        PaperInfo pi = getPaperInfoByTaskId(taskId);
        return toVO(pi);
    }

    @Override
    public void refreshPaperInfo(Long taskId) {
        PaperInfo pi = getPaperInfoByTaskId(taskId);
        // TODO: 重新调用 arXiv API 拉取论文信息
        log.info("refreshPaperInfo: taskId={}, arxivId={}", taskId, pi.getArxivId());
    }

    private PaperInfo getPaperInfoByTaskId(Long taskId) {
        PaperInfo pi = paperInfoMapper.selectOne(
                new LambdaQueryWrapper<PaperInfo>().eq(PaperInfo::getTaskId, taskId));
        if (pi == null) throw new BusinessException("论文信息不存在");
        return pi;
    }

    private PaperInfoVO toVO(PaperInfo pi) {
        PaperInfoVO vo = new PaperInfoVO();
        vo.setArxivId(pi.getArxivId()); vo.setTitle(pi.getTitle());
        vo.setAuthors(pi.getAuthors()); vo.setAbstractText(pi.getAbstractText());
        vo.setPublishedAt(pi.getPublishedAt()); vo.setPaperUrl(pi.getPaperUrl());
        return vo;
    }
}
