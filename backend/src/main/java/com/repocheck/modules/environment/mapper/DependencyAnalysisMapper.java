package com.repocheck.modules.environment.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.repocheck.modules.environment.entity.DependencyAnalysis;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DependencyAnalysisMapper extends BaseMapper<DependencyAnalysis> {
}
