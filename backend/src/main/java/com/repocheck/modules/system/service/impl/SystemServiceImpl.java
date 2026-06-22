package com.repocheck.modules.system.service.impl;

import com.repocheck.modules.system.service.SystemService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class SystemServiceImpl implements SystemService {

    private final RestTemplate restTemplate;

    @Value("${ai-service.base-url}")
    private String aiServiceBaseUrl;

    @Override
    public Map<String, Object> health() {
        return Map.of("status", "UP", "mysql", "UP", "redis", "UP", "minio", "UP");
    }

    @Override
    public Map<String, Object> aiHealth() {
        try {
            String result = restTemplate.getForObject(aiServiceBaseUrl + "/api/health", String.class);
            return Map.of("aiServiceStatus", "UP", "aiServiceUrl", aiServiceBaseUrl, "detail", result);
        } catch (Exception e) {
            log.error("AI health check failed", e);
            return Map.of("aiServiceStatus", "DOWN", "aiServiceUrl", aiServiceBaseUrl);
        }
    }

    @Override
    public Map<String, Object> getConfig() {
        return Map.of(
                "appName", "RepoCheck",
                "version", "1.0.0",
                "maxTaskPerUser", 10,
                "supportedPlatforms", new String[]{"arXiv", "GitHub", "GitLab"}
        );
    }
}
