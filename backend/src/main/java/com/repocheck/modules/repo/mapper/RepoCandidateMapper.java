package com.repocheck.modules.repo.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.repocheck.modules.repo.entity.RepoCandidate;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface RepoCandidateMapper extends BaseMapper<RepoCandidate> {
}
