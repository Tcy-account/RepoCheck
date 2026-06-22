package com.repocheck.modules.task.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.repocheck.modules.task.entity.PaperTask;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface PaperTaskMapper extends BaseMapper<PaperTask> {
}
