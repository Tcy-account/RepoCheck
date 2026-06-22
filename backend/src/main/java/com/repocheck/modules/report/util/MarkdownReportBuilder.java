package com.repocheck.modules.report.util;

import com.repocheck.modules.environment.entity.DependencyAnalysis;
import com.repocheck.modules.environment.entity.EnvironmentAnalysis;
import com.repocheck.modules.report.vo.ReportVO;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Markdown 报告生成器
 *
 * 基于 ReportVO + 可选环境分析数据生成结构化 Markdown 文本。
 * 不依赖数据库、不依赖 LLM。
 */
public class MarkdownReportBuilder {

    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd");
    private static final DateTimeFormatter DATE_TIME_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    /**
     * 生成完整 Markdown 报告（不含 V2 环境诊断）
     */
    public static String build(ReportVO vo) {
        return build(vo, null, null);
    }

    /**
     * 生成完整 Markdown 报告（含 V2 环境诊断）
     *
     * @param vo   报告主体数据
     * @param env  环境分析汇总（可为 null）
     * @param deps 依赖列表（可为 null）
     */
    public static String build(ReportVO vo, EnvironmentAnalysis env, List<DependencyAnalysis> deps) {
        StringBuilder md = new StringBuilder();

        md.append("# RepoCheck 论文复现可行性报告\n\n");

        // 一、论文信息
        appendPaperInfo(md, vo.getPaperInfo());

        // 二、仓库信息
        appendRepoInfo(md, vo.getRepoInfo());

        // 三、仓库完整度检查
        appendStructure(md, vo.getRepoAnalysis());

        // 四、评分结果
        appendScores(md, vo.getReport());

        // 五 ~ 九、报告文本
        appendReportSections(md, vo.getReport());

        // 十、环境诊断（V2）
        appendEnvironment(md, env, deps);

        // 十一、报告说明
        appendFooter(md);

        return md.toString();
    }

    // ══════════════════════════════════════════════
    // 一 ~ 四
    // ══════════════════════════════════════════════

    private static void appendPaperInfo(StringBuilder md, ReportVO.PaperInfoVO pi) {
        md.append("## 一、论文信息\n\n");
        if (pi == null) {
            md.append("暂无论文信息。\n\n");
            return;
        }
        md.append("- arXiv ID: ").append(nvl(pi.getArxivId())).append("\n");
        md.append("- 标题: ").append(nvl(pi.getTitle())).append("\n");
        md.append("- 作者: ").append(nvl(pi.getAuthors())).append("\n");
        md.append("- 发布时间: ").append(formatDate(pi.getPublishedAt())).append("\n");
        md.append("- 论文链接: ").append(nvl(pi.getPaperUrl())).append("\n");
        md.append("\n");
    }

    private static void appendRepoInfo(StringBuilder md, ReportVO.RepoInfoVO ri) {
        md.append("## 二、代码仓库信息\n\n");
        if (ri == null) {
            md.append("暂无仓库信息。\n\n");
            return;
        }
        md.append("- 平台: ").append(nvl(ri.getPlatform())).append("\n");
        md.append("- 仓库: ").append(nvl(ri.getRepoName())).append("\n");
        md.append("- 仓库地址: ").append(nvl(ri.getRepoUrl())).append("\n");
        md.append("- 所有者: ").append(nvl(ri.getOwner())).append("\n");
        md.append("- Star: ").append(ri.getStars() != null ? ri.getStars() : 0).append("\n");
        md.append("- Fork: ").append(ri.getForks() != null ? ri.getForks() : 0).append("\n");
        md.append("- 默认分支: ").append(nvl(ri.getDefaultBranch())).append("\n");
        md.append("- 最近更新: ").append(formatDateTime(ri.getLastUpdatedAt())).append("\n");

        String confidence = ri.getConfidence() != null
                ? String.format("%.0f%%", ri.getConfidence().multiply(BigDecimal.valueOf(100)))
                : "未知";
        md.append("- 仓库匹配置信度: ").append(confidence).append("\n");
        md.append("- 置信度说明: ").append(nvl(ri.getConfidenceReason())).append("\n");
        md.append("\n");
    }

    private static void appendStructure(StringBuilder md, ReportVO.RepoAnalysisVO ra) {
        md.append("## 三、仓库完整度检查\n\n");
        md.append("| 检查项 | 是否具备 |\n");
        md.append("|---|---|\n");

        if (ra == null) {
            String[] items = {"README", "依赖文件", "Conda 环境文件", "Dockerfile",
                    "License", "训练代码", "推理/Demo 代码", "数据集说明", "模型权重说明"};
            for (String item : items) {
                md.append("| ").append(item).append(" | 未知 |\n");
            }
        } else {
            md.append("| README | ").append(yn(ra.getHasReadme())).append(" |\n");
            md.append("| 依赖文件 (requirements/pyproject/setup/Pipfile) | ").append(yn(ra.getHasRequirements())).append(" |\n");
            md.append("| Conda 环境文件 (environment.yml) | ").append(yn(ra.getHasEnvironmentYml())).append(" |\n");
            md.append("| Dockerfile | ").append(yn(ra.getHasDockerfile())).append(" |\n");
            md.append("| License | ").append(yn(ra.getHasLicense())).append(" |\n");
            md.append("| 训练代码 | ").append(yn(ra.getHasTrainCode())).append(" |\n");
            md.append("| 推理/Demo 代码 | ").append(yn(ra.getHasInferenceCode())).append(" |\n");
            md.append("| 数据集说明 | ").append(yn(ra.getHasDatasetDoc())).append(" |\n");
            md.append("| 模型权重说明 | ").append(yn(ra.getHasWeightDoc())).append(" |\n");
        }
        md.append("\n");
    }

    private static void appendScores(StringBuilder md, ReportVO.ReportDataVO rd) {
        md.append("## 四、评分结果\n\n");
        md.append("| 评分项 | 分数 |\n");
        md.append("|---|---|\n");

        if (rd == null) {
            md.append("| 复现可行性评分 | 未知 |\n");
            md.append("| 仓库完整度评分 | 未知 |\n");
            md.append("| 环境友好度评分 | 未知 |\n");
            md.append("| 风险等级 | 未知 |\n");
        } else {
            md.append("| 复现可行性评分 | ")
                    .append(rd.getReproducibilityScore() != null ? rd.getReproducibilityScore() : "—")
                    .append("/100 |\n");
            md.append("| 仓库完整度评分 | ")
                    .append(rd.getCompletenessScore() != null ? rd.getCompletenessScore() : "—")
                    .append("/100 |\n");
            md.append("| 环境友好度评分 | ")
                    .append(rd.getEnvironmentScore() != null ? rd.getEnvironmentScore() : "—")
                    .append("/100 |\n");
            md.append("| 风险等级 | ").append(nvl(rd.getRiskLevel())).append(" |\n");
        }
        md.append("\n");
    }

    // ══════════════════════════════════════════════
    // 五 ~ 九
    // ══════════════════════════════════════════════

    private static void appendReportSections(StringBuilder md, ReportVO.ReportDataVO rd) {
        // 五、论文方法概述
        md.append("## 五、论文方法概述\n\n");
        md.append(nvl(rd != null ? rd.getMethodSummary() : null)).append("\n\n");

        // 六、可能创新点
        md.append("## 六、可能创新点\n\n");
        md.append(nvl(rd != null ? rd.getInnovationSummary() : null)).append("\n\n");

        // 七、建议复现步骤
        md.append("## 七、建议复现步骤\n\n");
        md.append(nvl(rd != null ? rd.getReproduceSteps() : null)).append("\n\n");

        // 八、风险提示
        md.append("## 八、风险提示\n\n");
        md.append(nvl(rd != null ? rd.getRiskTips() : null)).append("\n\n");

        // 九、最终建议
        md.append("## 九、最终建议\n\n");
        md.append(nvl(rd != null ? rd.getFinalAdvice() : null)).append("\n\n");
    }

    // ══════════════════════════════════════════════
    // 十、V2 环境诊断
    // ══════════════════════════════════════════════

    private static void appendEnvironment(StringBuilder md, EnvironmentAnalysis env,
                                          List<DependencyAnalysis> deps) {
        md.append("## 十、环境诊断\n\n");

        if (env == null) {
            md.append("> 尚未进行 V2 环境诊断。请在任务详情页点击「开始环境分析」后重新导出报告。\n\n");
            return;
        }

        // ── 环境概览 ──
        md.append("### 环境概览\n\n");
        md.append("| 项目 | 结果 |\n");
        md.append("|---|---|\n");
        md.append("| 环境评分 | ").append(nvlScore(env.getEnvironmentScore())).append("/100 |\n");
        md.append("| 环境风险等级 | ").append(nvl(env.getRiskLevel())).append(" |\n");
        md.append("| 主框架 | ").append(nvl(env.getMainFramework())).append(" |\n");
        md.append("| 框架版本 | ").append(nvl(env.getFrameworkVersion())).append(" |\n");
        md.append("| Python 版本 | ").append(nvl(env.getPythonVersion())).append(" |\n");
        md.append("| CUDA 版本 | ").append(nvl(env.getCudaVersion())).append(" |\n");
        md.append("| 是否需要 GPU | ").append(
                env.getRequiresGpu() != null && env.getRequiresGpu() == 1 ? "是" : "否").append(" |\n");
        md.append("| 是否提供 Docker | ").append(
                env.getHasDocker() != null && env.getHasDocker() == 1 ? "是" : "否").append(" |\n");
        md.append("| Docker 基础镜像 | ").append(nvl(env.getDockerBaseImage())).append(" |\n");
        md.append("\n");

        // ── 环境风险评分 ──
        md.append("### 环境风险评分\n\n");
        md.append("| 评分项 | 分数 |\n");
        md.append("|---|---|\n");
        md.append("| 依赖风险分 | ").append(nvlScore(env.getDependencyRiskScore())).append("/100 |\n");
        md.append("| CUDA 风险分 | ").append(nvlScore(env.getCudaRiskScore())).append("/100 |\n");
        md.append("| Docker 成熟度 | ").append(nvlScore(env.getDockerReadinessScore())).append("/100 |\n");
        md.append("\n");
        md.append("> 依赖风险分和 CUDA 风险分越高，表示环境配置失败风险越大；" +
                "Docker 成熟度越高，表示容器化复现条件越好。\n\n");

        // ── 风险摘要 ──
        if (env.getRiskSummary() != null && !env.getRiskSummary().isBlank()) {
            md.append("### 环境风险摘要\n\n");
            md.append(env.getRiskSummary()).append("\n\n");
        }

        // ── 安装建议 ──
        if (env.getInstallAdvice() != null && !env.getInstallAdvice().isBlank()) {
            md.append("### 安装建议\n\n");
            md.append("```\n");
            md.append(env.getInstallAdvice());
            md.append("\n```\n\n");
        }

        // ── 高风险依赖 ──
        appendHighRiskDependencies(md, deps);
    }

    private static void appendHighRiskDependencies(StringBuilder md, List<DependencyAnalysis> deps) {
        md.append("### 高风险依赖\n\n");

        if (deps == null || deps.isEmpty()) {
            md.append("未检测到高风险依赖。\n\n");
            return;
        }

        List<DependencyAnalysis> highRisk = deps.stream()
                .filter(d -> "HIGH".equalsIgnoreCase(d.getRiskLevel()))
                .collect(Collectors.toList());

        if (highRisk.isEmpty()) {
            md.append("未检测到高风险依赖。\n\n");
            return;
        }

        md.append("| 包名 | 版本 | 来源 | 文件 | 风险原因 |\n");
        md.append("|---|---|---|---|---|\n");

        int limit = Math.min(highRisk.size(), 20);
        for (int i = 0; i < limit; i++) {
            DependencyAnalysis d = highRisk.get(i);
            md.append("| ").append(escape(d.getPackageName()))
                    .append(" | ").append(escape(nvlInline(d.getVersionSpec())))
                    .append(" | ").append(escape(nvlInline(d.getSource())))
                    .append(" | ").append(escape(nvlInline(d.getFilePath())))
                    .append(" | ").append(escape(nvlInline(d.getRiskReason())))
                    .append(" |\n");
        }

        if (highRisk.size() > 20) {
            md.append("\n> 仅展示前 20 条高风险依赖，共 ").append(highRisk.size()).append(" 条。\n");
        }
        md.append("\n");
    }

    // ══════════════════════════════════════════════
    // 十一、报告说明
    // ══════════════════════════════════════════════

    private static void appendFooter(StringBuilder md) {
        md.append("## 十一、报告说明\n\n");
        md.append("> **说明：**\n");
        md.append("> \n");
        md.append("> 本报告由 RepoCheck V2 基于论文元信息、GitHub 仓库结构和 README 文档进行静态分析生成。\n");
        md.append("> V2 不会运行代码、不会安装依赖、不会下载数据集或模型权重。\n");
        md.append("> 报告仅用于复现前风险评估，不能保证代码一定可以成功运行。\n");
    }

    // ── 辅助方法 ──

    private static String yn(Boolean b) {
        return Boolean.TRUE.equals(b) ? "是" : "否";
    }

    private static String nvl(String s) {
        return (s == null || s.isBlank()) ? "未知" : s;
    }

    /** 表格内用的 nvl — 避免换行 */
    private static String nvlInline(String s) {
        return (s == null || s.isBlank()) ? "—" : s;
    }

    private static String nvlScore(Integer score) {
        return score != null ? String.valueOf(score) : "—";
    }

    private static String escape(String s) {
        if (s == null) return "";
        return s.replace("|", "\\|").replace("\n", " ").replace("\r", "");
    }

    private static String formatDate(LocalDate d) {
        return d != null ? d.format(DATE_FMT) : "未知";
    }

    private static String formatDateTime(LocalDateTime dt) {
        return dt != null ? dt.format(DATE_TIME_FMT) : "未知";
    }
}
