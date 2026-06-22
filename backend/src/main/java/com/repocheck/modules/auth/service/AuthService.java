package com.repocheck.modules.auth.service;

import com.repocheck.modules.auth.dto.*;
import com.repocheck.modules.auth.vo.*;

public interface AuthService {
    LoginVO register(RegisterRequest request);
    LoginVO login(LoginRequest request);
    void logout();
    CurrentUserVO getCurrentUser();
}
