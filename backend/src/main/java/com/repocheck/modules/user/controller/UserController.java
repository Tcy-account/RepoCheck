package com.repocheck.modules.user.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.repocheck.common.Result;
import com.repocheck.modules.user.dto.UpdatePasswordRequest;
import com.repocheck.modules.user.dto.UpdateUserRequest;
import com.repocheck.modules.user.service.UserService;
import com.repocheck.modules.user.vo.UserVO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/me")
    public Result<UserVO> getMe() {
        Long userId = StpUtil.getLoginIdAsLong();
        return Result.success(userService.getCurrentUser(userId));
    }

    @PutMapping("/me")
    public Result<Void> updateMe(@Valid @RequestBody UpdateUserRequest request) {
        Long userId = StpUtil.getLoginIdAsLong();
        userService.updateUser(userId, request);
        return Result.success();
    }

    @PutMapping("/me/password")
    public Result<Void> updatePassword(@Valid @RequestBody UpdatePasswordRequest request) {
        Long userId = StpUtil.getLoginIdAsLong();
        userService.updatePassword(userId, request);
        return Result.success();
    }
}
