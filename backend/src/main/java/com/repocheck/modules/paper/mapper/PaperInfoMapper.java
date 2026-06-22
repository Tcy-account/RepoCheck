package com.repocheck.modules.paper.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.repocheck.modules.paper.entity.PaperInfo;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface PaperInfoMapper extends BaseMapper<PaperInfo> {
}
