package com.repocheck.modules.system.controller;

import com.repocheck.common.Result;
import com.repocheck.modules.system.service.SystemService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/system")
@RequiredArgsConstructor
public class SystemController {

    private final SystemService systemService;

    @GetMapping("/health")
    public Result<Map<String, Object>> health() {
        return Result.success(systemService.health());
    }

    @GetMapping("/ai-health")
    public Result<Map<String, Object>> aiHealth() {
        return Result.success(systemService.aiHealth());
    }

    @GetMapping("/config")
    public Result<Map<String, Object>> config() {
        return Result.success(systemService.getConfig());
    }
}
