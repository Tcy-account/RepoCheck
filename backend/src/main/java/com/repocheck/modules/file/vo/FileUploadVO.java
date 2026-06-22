package com.repocheck.modules.file.vo;

import lombok.Data;

@Data
public class FileUploadVO {
    private String fileId;
    private String fileName;
    private Long fileSize;
}
