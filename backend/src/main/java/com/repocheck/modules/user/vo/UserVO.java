package com.repocheck.modules.user.vo;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class UserVO {
    private Long id;
    private String username;
    private String email;
    private LocalDateTime createTime;
}
