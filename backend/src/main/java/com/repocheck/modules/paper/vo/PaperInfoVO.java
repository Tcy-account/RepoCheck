package com.repocheck.modules.paper.vo;

import lombok.Data;
import java.time.LocalDate;

@Data
public class PaperInfoVO {
    private String arxivId;
    private String title;
    private String authors;
    private String abstractText;
    private LocalDate publishedAt;
    private String paperUrl;
}
