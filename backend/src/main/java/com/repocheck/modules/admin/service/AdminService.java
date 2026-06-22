package com.repocheck.modules.admin.service;

import java.util.Map;

public interface AdminService {
    Map<String, Object> listAllTasks(int page, int size);
    Map<String, Object> listAllUsers(int page, int size);
    Map<String, Object> listFailedTasks(int page, int size);
}
