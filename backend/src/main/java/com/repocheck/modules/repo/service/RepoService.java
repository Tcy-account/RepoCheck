package com.repocheck.modules.repo.service;

import com.repocheck.modules.repo.dto.*;
import com.repocheck.modules.repo.vo.*;
import java.util.List;

public interface RepoService {
    RepoInfoVO getRepoInfo(Long taskId);
    List<RepoCandidateVO> getCandidates(Long taskId);
    void updateRepo(Long taskId, UpdateRepoRequest request);
    void searchRepo(Long taskId);
}
