package com.repocheck.modules.paper.service;

import com.repocheck.modules.paper.vo.*;

public interface PaperService {
    PaperInfoVO getPaperInfo(Long taskId);
    void refreshPaperInfo(Long taskId);
}
