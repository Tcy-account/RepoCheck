package com.repocheck.modules.user.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.repocheck.modules.user.dto.UpdatePasswordRequest;
import com.repocheck.modules.user.dto.UpdateUserRequest;
import com.repocheck.modules.user.entity.User;
import com.repocheck.modules.user.mapper.UserMapper;
import com.repocheck.modules.user.service.UserService;
import com.repocheck.modules.user.vo.UserVO;
import com.repocheck.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final BCryptPasswordEncoder passwordEncoder;

    @Override
    public UserVO getCurrentUser(Long userId) {
        User user = getUserById(userId);
        UserVO vo = new UserVO();
        vo.setId(user.getId()); vo.setUsername(user.getUsername());
        vo.setEmail(user.getEmail()); vo.setCreateTime(user.getCreateTime());
        return vo;
    }

    @Override
    public void updateUser(Long userId, UpdateUserRequest request) {
        User user = getUserById(userId);
        if (request.getEmail() != null) {
            user.setEmail(request.getEmail());
        }
        userMapper.updateById(user);
    }

    @Override
    public void updatePassword(Long userId, UpdatePasswordRequest request) {
        User user = getUserById(userId);
        // 校验旧密码
        if (!passwordEncoder.matches(request.getOldPassword(), user.getPassword())) {
            throw new BusinessException("旧密码不正确");
        }
        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        userMapper.updateById(user);
    }

    private User getUserById(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) throw new BusinessException("用户不存在");
        return user;
    }
}
