package com.repocheck.modules.file.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.repocheck.modules.file.entity.FileInfo;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface FileInfoMapper extends BaseMapper<FileInfo> {
}
