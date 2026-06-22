package com.repocheck.modules.file.service;

import com.repocheck.modules.file.vo.*;
import org.springframework.web.multipart.MultipartFile;

public interface FileService {
    FileUploadVO upload(MultipartFile file, String type);
    FileDownloadVO getDownloadUrl(String fileId);
    void delete(String fileId);
}
