package com.repocheck.modules.analysis.service;

import com.repocheck.modules.analysis.vo.*;
import java.util.List;

public interface AnalysisService {
    RepoAnalysisVO getAnalysis(Long taskId);
    void rebuildAnalysis(Long taskId);
    List<String> getFileList(Long taskId);
    ReadmeAnalysisVO getReadmeAnalysis(Long taskId);
}
