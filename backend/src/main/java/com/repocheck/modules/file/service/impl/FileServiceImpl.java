package com.repocheck.modules.file.service.impl;

import com.repocheck.modules.file.service.FileService;
import com.repocheck.modules.file.vo.FileDownloadVO;
import com.repocheck.modules.file.vo.FileUploadVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

@Slf4j
@Service
public class FileServiceImpl implements FileService {

    @Override
    public FileUploadVO upload(MultipartFile file, String type) {
        // TODO: V1 MinIO 占位
        FileUploadVO vo = new FileUploadVO();
        vo.setFileId("placeholder-" + System.currentTimeMillis());
        vo.setFileName(file.getOriginalFilename());
        vo.setFileSize(file.getSize());
        log.info("File upload placeholder: name={}, size={}, type={}",
                file.getOriginalFilename(), file.getSize(), type);
        return vo;
    }

    @Override
    public FileDownloadVO getDownloadUrl(String fileId) {
        // TODO: V1 MinIO 占位
        FileDownloadVO vo = new FileDownloadVO();
        vo.setDownloadUrl("http://localhost:9000/repocheck/" + fileId);
        vo.setExpireAt("2025-12-31T23:59:59");
        return vo;
    }

    @Override
    public void delete(String fileId) {
        // TODO: V1 MinIO 占位
        log.info("File delete placeholder: fileId={}", fileId);
    }
}
