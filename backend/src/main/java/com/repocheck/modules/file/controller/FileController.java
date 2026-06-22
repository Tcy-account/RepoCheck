package com.repocheck.modules.file.controller;

import com.repocheck.common.Result;
import com.repocheck.modules.file.service.FileService;
import com.repocheck.modules.file.vo.FileDownloadVO;
import com.repocheck.modules.file.vo.FileUploadVO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/files")
@RequiredArgsConstructor
public class FileController {

    private final FileService fileService;

    @PostMapping("/upload")
    public Result<FileUploadVO> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "type", defaultValue = "REPORT_MD") String type) {
        return Result.success(fileService.upload(file, type));
    }

    @GetMapping("/{fileId}/download-url")
    public Result<FileDownloadVO> downloadUrl(@PathVariable String fileId) {
        return Result.success(fileService.getDownloadUrl(fileId));
    }

    @DeleteMapping("/{fileId}")
    public Result<Void> delete(@PathVariable String fileId) {
        fileService.delete(fileId);
        return Result.success();
    }
}
