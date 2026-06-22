package com.repocheck.modules.analysis.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.repocheck.modules.analysis.entity.RepoAnalysis;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface RepoAnalysisMapper extends BaseMapper<RepoAnalysis> {
}
