package com.repocheck.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * RestTemplate 配置 (用于调用 FastAPI AI 服务)
 *
 * - connectTimeout: 5 秒
 * - readTimeout: 60 秒（AI 分析仓库可能较慢）
 */
@Configuration
public class RestTemplateConfig {

    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);   // 5 秒
        factory.setReadTimeout(60_000);    // 60 秒
        return new RestTemplate(factory);
    }
}
