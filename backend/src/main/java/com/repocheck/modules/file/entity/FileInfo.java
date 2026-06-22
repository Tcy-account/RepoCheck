package com.repocheck.modules.file.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("file_info")
public class FileInfo {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String fileId;
    private String fileName;
    private Long fileSize;
    private String fileType;
    private String minioPath;
    private Long taskId;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
