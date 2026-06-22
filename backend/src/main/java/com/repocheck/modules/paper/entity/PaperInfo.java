package com.repocheck.modules.paper.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDate;

@Data
@TableName("paper_info")
public class PaperInfo {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long taskId;
    private String arxivId;
    private String title;
    private String authors;
    private String abstractText;
    private LocalDate publishedAt;
    private String paperUrl;
}
