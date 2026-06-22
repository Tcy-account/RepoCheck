package com.repocheck.modules.repo.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class UpdateRepoRequest {
    @NotBlank
    private String repoUrl;
    @NotBlank
    private String platform;
}
