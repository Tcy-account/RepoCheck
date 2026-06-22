package com.repocheck.modules.auth.vo;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class CurrentUserVO {
    private Long id;
    private String username;
    private String email;
    private LocalDateTime createTime;
}
