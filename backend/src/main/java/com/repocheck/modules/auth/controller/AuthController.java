package com.repocheck.modules.auth.controller;

import com.repocheck.common.Result;
import com.repocheck.modules.auth.dto.LoginRequest;
import com.repocheck.modules.auth.dto.RegisterRequest;
import com.repocheck.modules.auth.service.AuthService;
import com.repocheck.modules.auth.vo.CurrentUserVO;
import com.repocheck.modules.auth.vo.LoginVO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public Result<LoginVO> register(@Valid @RequestBody RegisterRequest request) {
        return Result.success(authService.register(request));
    }

    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody LoginRequest request) {
        return Result.success(authService.login(request));
    }

    @PostMapping("/logout")
    public Result<Void> logout() {
        authService.logout();
        return Result.success();
    }

    @GetMapping("/me")
    public Result<CurrentUserVO> me() {
        return Result.success(authService.getCurrentUser());
    }
}
