package com.repocheck.modules.paper.controller;

import com.repocheck.common.Result;
import com.repocheck.modules.paper.service.PaperService;
import com.repocheck.modules.paper.vo.PaperInfoVO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/tasks/{taskId}/paper")
@RequiredArgsConstructor
public class PaperController {

    private final PaperService paperService;

    @GetMapping
    public Result<PaperInfoVO> getPaper(@PathVariable Long taskId) {
        return Result.success(paperService.getPaperInfo(taskId));
    }

    @PostMapping("/refresh")
    public Result<Void> refresh(@PathVariable Long taskId) {
        paperService.refreshPaperInfo(taskId);
        return Result.success();
    }
}
