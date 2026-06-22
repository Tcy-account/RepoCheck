package com.repocheck.modules.file.vo;

import lombok.Data;

@Data
public class FileDownloadVO {
    private String downloadUrl;
    private String expireAt;
}
