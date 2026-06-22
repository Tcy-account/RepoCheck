package com.repocheck.modules.system.service;

import java.util.Map;

public interface SystemService {
    Map<String, Object> health();
    Map<String, Object> aiHealth();
    Map<String, Object> getConfig();
}
