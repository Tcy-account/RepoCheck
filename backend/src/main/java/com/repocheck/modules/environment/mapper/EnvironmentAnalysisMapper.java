package com.repocheck.modules.environment.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.repocheck.modules.environment.entity.EnvironmentAnalysis;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface EnvironmentAnalysisMapper extends BaseMapper<EnvironmentAnalysis> {
}
