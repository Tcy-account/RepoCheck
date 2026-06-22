package com.repocheck.modules.user.service;

import com.repocheck.modules.user.dto.*;
import com.repocheck.modules.user.vo.*;

public interface UserService {
    UserVO getCurrentUser(Long userId);
    void updateUser(Long userId, UpdateUserRequest request);
    void updatePassword(Long userId, UpdatePasswordRequest request);
}
