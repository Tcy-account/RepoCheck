package com.repocheck.modules.admin.service.impl;

import com.repocheck.modules.admin.service.AdminService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;

@Slf4j
@Service
public class AdminServiceImpl implements AdminService {

    @Override
    public Map<String, Object> listAllTasks(int page, int size) {
        throw new ResponseStatusException(HttpStatus.NOT_IMPLEMENTED, "Admin API not available in V1");
    }

    @Override
    public Map<String, Object> listAllUsers(int page, int size) {
        throw new ResponseStatusException(HttpStatus.NOT_IMPLEMENTED, "Admin API not available in V1");
    }

    @Override
    public Map<String, Object> listFailedTasks(int page, int size) {
        throw new ResponseStatusException(HttpStatus.NOT_IMPLEMENTED, "Admin API not available in V1");
    }
}
