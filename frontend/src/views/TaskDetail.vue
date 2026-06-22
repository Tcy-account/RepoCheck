<template>
  <div class="task-detail-page">
    <!-- ============ 顶部概览区 ============ -->
    <div class="page-header" v-if="report">
      <div class="header-left">
        <el-button @click="$router.back()" :icon="'ArrowLeft'">返回</el-button>
      </div>
      <div class="header-center">
        <h2 class="paper-title">{{ report.paperInfo.title || '未知论文' }}</h2>
        <div class="header-meta">
          <el-tag v-if="report.paperInfo.arxivId" type="info" size="small" effect="plain">
            {{ report.paperInfo.arxivId }}
          </el-tag>
          <el-tag :type="riskTagType(report.report.riskLevel)" size="small" effect="dark" style="margin-left: 8px">
            {{ riskLabel(report.report.riskLevel) }}
          </el-tag>
          <span class="score-inline" :style="{ color: scoreColor(report.report.reproducibilityScore) }">
            复现评分 {{ report.report.reproducibilityScore }}/100
          </span>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="handleRefreshReport" :loading="refreshLoading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="success" :loading="exportLoading" @click="handleExportMarkdown">
          <el-icon><Download /></el-icon>
          导出 Markdown
        </el-button>
      </div>
    </div>

    <!-- ============ 加载 / 错误 / 空状态 ============ -->
    <el-card v-if="loading" class="info-card" shadow="never">
      <el-skeleton :rows="6" animated />
    </el-card>

    <el-card v-else-if="loadError" class="info-card" shadow="never">
      <el-result icon="error" title="加载失败" :sub-title="loadError">
        <template #extra>
          <el-button type="primary" @click="loadData">重试</el-button>
        </template>
      </el-result>
    </el-card>

    <!-- 任务未完成 - 报告尚未生成 -->
    <template v-else-if="task && !report">
      <!-- 任务状态 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <span>任务状态</span>
          <el-tag :type="statusType(task.status)" style="margin-left: 12px">
            {{ statusLabel(task.status) }}
          </el-tag>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务 ID">{{ task.id }}</el-descriptions-item>
          <el-descriptions-item label="论文链接">
            <a :href="task.paperUrl" target="_blank">{{ task.paperUrl }}</a>
          </el-descriptions-item>
          <el-descriptions-item label="论文标题">{{ task.paperTitle }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ task.createTime }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="task.status === 'FAILED'" style="margin-top: 12px;">
          <el-alert :title="task.errorMessage || '任务执行失败'" type="error" show-icon />
          <el-button type="primary" style="margin-top: 8px" @click="handleRetry">重试任务</el-button>
        </div>
      </el-card>

      <!-- 时间线 -->
      <el-card v-if="taskStore.currentTimeline.length > 0" class="info-card" shadow="never">
        <template #header><span>任务进度</span></template>
        <el-timeline>
          <el-timeline-item
            v-for="item in taskStore.currentTimeline"
            :key="item.id"
            :timestamp="item.createTime"
            :color="timelineColor(item.status)"
            placement="top"
          >
            <div>
              <el-tag :type="statusType(item.status)" size="small" style="margin-right: 8px">
                {{ statusLabel(item.status) }}
              </el-tag>
              <span style="color: #606266; font-size: 14px;">{{ item.message }}</span>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <!-- 手动指定仓库 -->
      <el-card class="info-card" shadow="never">
        <template #header><span>手动指定仓库</span></template>
        <el-form :inline="true" :model="manualRepoForm" @submit.prevent>
          <el-form-item label="GitHub 仓库地址" style="width: 420px">
            <el-input
              v-model="manualRepoForm.url"
              placeholder="例如 https://github.com/huggingface/transformers"
              clearable
              :disabled="manualRepoLoading"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="manualRepoLoading"
              :disabled="!manualRepoForm.url.trim()"
              @click="handleManualRepo"
            >
              保存并重新分析
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 进行中 / 失败提示 -->
      <el-card class="info-card" shadow="never">
        <template #header><span>分析报告</span></template>
        <template v-if="isTerminal(task.status)">
          <template v-if="task.status === 'FAILED'">
            <el-result icon="error" title="分析失败" :sub-title="task.errorMessage || '未知错误'">
              <template #extra>
                <el-button type="primary" @click="handleRetry">重试任务</el-button>
              </template>
            </el-result>
          </template>
          <template v-else>
            <el-result icon="warning" title="报告数据暂未生成" sub-title="请稍后刷新页面查看">
              <template #extra>
                <el-button @click="handleRefreshReport">刷新</el-button>
              </template>
            </el-result>
          </template>
        </template>
        <template v-else>
          <div class="analyzing-hint">
            <el-icon class="is-loading" :size="28"><Loading /></el-icon>
            <p>报告生成中：{{ statusLabel(task.status) }}</p>
            <p class="hint-sub">任务完成后将自动加载报告</p>
          </div>
        </template>
      </el-card>
    </template>

    <!-- ============ 报告内容 ============ -->
    <template v-if="report">
      <!-- 评分卡片区 -->
      <el-row :gutter="20" class="score-row">
        <el-col :span="8">
          <el-card class="score-card" shadow="never">
            <div class="score-card-inner">
              <el-progress
                type="circle"
                :percentage="report.report.reproducibilityScore"
                :width="130"
                :stroke-width="12"
                :color="scoreColor(report.report.reproducibilityScore)"
              >
                <span class="score-number" :style="{ color: scoreColor(report.report.reproducibilityScore) }">
                  {{ report.report.reproducibilityScore }}
                </span>
              </el-progress>
              <div class="score-title">复现可行性评分</div>
              <div class="score-desc">综合评估论文代码可复现的可行性</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="score-card" shadow="never">
            <div class="score-card-inner">
              <el-progress
                type="circle"
                :percentage="report.report.completenessScore"
                :width="130"
                :stroke-width="12"
                :color="scoreColor(report.report.completenessScore)"
              >
                <span class="score-number" :style="{ color: scoreColor(report.report.completenessScore) }">
                  {{ report.report.completenessScore }}
                </span>
              </el-progress>
              <div class="score-title">仓库完整度评分</div>
              <div class="score-desc">检查仓库关键文件是否齐全</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="score-card" shadow="never">
            <div class="score-card-inner">
              <el-progress
                type="circle"
                :percentage="report.report.environmentScore"
                :width="130"
                :stroke-width="12"
                :color="scoreColor(report.report.environmentScore)"
              >
                <span class="score-number" :style="{ color: scoreColor(report.report.environmentScore) }">
                  {{ report.report.environmentScore }}
                </span>
              </el-progress>
              <div class="score-title">环境友好度评分</div>
              <div class="score-desc">评估依赖安装与运行环境的复杂度</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 论文信息区 -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon size="18"><Document /></el-icon>
            <span>论文信息</span>
          </div>
        </template>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="标题" :span="2">{{ report.paperInfo.title || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="arXiv ID">{{ report.paperInfo.arxivId || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="作者">{{ report.paperInfo.authors || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="发布时间">{{ report.paperInfo.publishedAt || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="论文链接">
            <a v-if="report.paperInfo.paperUrl" :href="report.paperInfo.paperUrl" target="_blank">
              {{ report.paperInfo.paperUrl }}
            </a>
            <span v-else>暂无</span>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="report.paperInfo.abstractText" class="abstract-section">
          <div class="abstract-toggle" @click="abstractExpanded = !abstractExpanded">
            <span>摘要</span>
            <el-icon>
              <ArrowDown v-if="!abstractExpanded" />
              <ArrowUp v-else />
            </el-icon>
          </div>
          <div v-show="abstractExpanded" class="abstract-content">
            {{ report.paperInfo.abstractText }}
          </div>
        </div>
      </el-card>

      <!-- 仓库信息区 -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon size="18"><FolderOpened /></el-icon>
            <span>代码仓库</span>
          </div>
        </template>
        <template v-if="report.repoInfo && report.repoInfo.repoUrl">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="平台">{{ report.repoInfo.platform || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="仓库">
              <a :href="report.repoInfo.repoUrl" target="_blank">
                {{ report.repoInfo.owner }}/{{ report.repoInfo.repoName }}
              </a>
            </el-descriptions-item>
            <el-descriptions-item label="Stars">{{ report.repoInfo.stars ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="Forks">{{ report.repoInfo.forks ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="默认分支">{{ report.repoInfo.defaultBranch || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="最近更新">{{ report.repoInfo.lastUpdatedAt || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="匹配置信度" :span="2">
              <div class="confidence-row">
                <el-progress
                  :percentage="Math.round((report.repoInfo.confidence ?? 0) * 100)"
                  :stroke-width="14"
                  style="flex: 1; max-width: 300px"
                  :color="report.repoInfo.confidence >= 0.7 ? '#67c23a' : report.repoInfo.confidence >= 0.4 ? '#e6a23c' : '#f56c6c'"
                />
                <span class="confidence-text">{{ report.repoInfo.confidenceReason || '' }}</span>
              </div>
            </el-descriptions-item>
          </el-descriptions>
          <!-- 手动指定仓库入口 -->
          <el-form :inline="true" :model="manualRepoForm" @submit.prevent style="margin-top: 16px;">
            <el-form-item label="重新指定" style="width: 380px">
              <el-input
                v-model="manualRepoForm.url"
                placeholder="输入新的 GitHub 仓库地址"
                clearable
                :disabled="manualRepoLoading"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="manualRepoLoading"
                :disabled="!manualRepoForm.url.trim()"
                @click="handleManualRepo"
              >
                重新分析
              </el-button>
            </el-form-item>
          </el-form>
        </template>
        <template v-else>
          <div class="empty-state">
            <el-empty description="未找到可信代码仓库" :image-size="80" />
            <p class="empty-tip">可尝试手动指定仓库重新分析</p>
            <el-form :inline="true" :model="manualRepoForm" @submit.prevent style="margin-top: 16px">
              <el-form-item label="GitHub 地址" style="width: 380px">
                <el-input
                  v-model="manualRepoForm.url"
                  placeholder="https://github.com/owner/repo"
                  clearable
                  :disabled="manualRepoLoading"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="manualRepoLoading"
                  :disabled="!manualRepoForm.url.trim()"
                  @click="handleManualRepo"
                >
                  保存并分析
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </template>
      </el-card>

      <!-- ============ V2.0 环境诊断 ============ -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon size="18"><Setting /></el-icon>
            <span>环境诊断</span>
            <el-button
              v-if="envAnalysis"
              size="small"
              type="primary"
              :loading="envRebuildLoading"
              :icon="'Refresh'"
              @click="handleRebuildAnalysis"
              style="margin-left: auto"
            >
              重新分析环境
            </el-button>
            <span v-else-if="envNotGenerated" style="margin-left: auto">
              <el-button
                v-if="report?.repoInfo?.repoUrl"
                size="small"
                type="primary"
                :loading="envRebuildLoading"
                @click="handleRebuildAnalysis"
              >
                开始环境分析
              </el-button>
              <el-tooltip v-else content="任务需完成且存在仓库信息后才能进行环境分析" placement="top">
                <el-button size="small" type="primary" disabled>
                  开始环境分析
                </el-button>
              </el-tooltip>
            </span>
          </div>
        </template>

        <!-- 加载 -->
        <el-skeleton v-if="envLoading" :rows="4" animated />

        <!-- 尚未生成 -->
        <template v-else-if="envNotGenerated">
          <div class="env-empty">
            <el-empty description="尚未进行环境分析，点击按钮开始分析" :image-size="60" />
          </div>
        </template>

        <!-- 已分析 -->
        <template v-else-if="envAnalysis">
          <!-- 顶部指标条 -->
          <el-row :gutter="16" class="env-metrics-row">
            <el-col :span="6">
              <div class="env-metric-item">
                <span class="env-metric-label">环境评分</span>
                <el-progress
                  type="circle"
                  :percentage="envAnalysis.environmentScore ?? 0"
                  :width="90"
                  :stroke-width="8"
                  :color="envScoreColor(envAnalysis.environmentScore ?? 0)"
                >
                  <span class="env-metric-score" :style="{ color: envScoreColor(envAnalysis.environmentScore ?? 0) }">
                    {{ envAnalysis.environmentScore ?? '-' }}
                  </span>
                </el-progress>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="env-metric-item">
                <span class="env-metric-label">风险等级</span>
                <el-tag :type="envScoreType(envAnalysis.environmentScore ?? 0)" size="large" effect="dark">
                  {{ riskLabel(envAnalysis.riskLevel || '') }}
                </el-tag>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="env-metric-item">
                <span class="env-metric-label">主框架</span>
                <span class="env-metric-value">{{ envAnalysis.mainFramework || '未识别' }}</span>
                <span v-if="envAnalysis.frameworkVersion" class="env-metric-sub">
                  {{ envAnalysis.frameworkVersion }}
                </span>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="env-metric-item">
                <span class="env-metric-label">Python 版本</span>
                <span class="env-metric-value">{{ envAnalysis.pythonVersion || '暂无' }}</span>
              </div>
            </el-col>
          </el-row>

          <el-row :gutter="16" class="env-metrics-row">
            <el-col :span="6">
              <div class="env-metric-item">
                <span class="env-metric-label">CUDA 版本</span>
                <span class="env-metric-value">{{ envAnalysis.cudaVersion || '暂无' }}</span>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="env-metric-item">
                <span class="env-metric-label">需要 GPU</span>
                <el-tag :type="envAnalysis.requiresGpu ? 'danger' : 'info'" size="small" effect="plain">
                  {{ envAnalysis.requiresGpu ? '是' : '否' }}
                </el-tag>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="env-metric-item">
                <span class="env-metric-label">Docker</span>
                <el-tag :type="envAnalysis.hasDocker ? 'success' : 'info'" size="small" effect="plain">
                  {{ envAnalysis.hasDocker ? '有' : '无' }}
                </el-tag>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="env-metric-item">
                <span class="env-metric-label">Docker 镜像</span>
                <span class="env-metric-value env-metric-small">{{ envAnalysis.dockerBaseImage || '暂无' }}</span>
              </div>
            </el-col>
          </el-row>

          <el-divider />

          <!-- 子评分 -->
          <el-row :gutter="16" class="env-subscores-row">
            <el-col :span="8">
              <div class="env-subscore-item">
                <span class="env-subscore-label">依赖风险分</span>
                <el-progress
                  :percentage="envAnalysis.dependencyRiskScore ?? 0"
                  :color="riskScoreColor(envAnalysis.dependencyRiskScore ?? 0)"
                  :stroke-width="10"
                />
                <el-tag :type="riskScoreType(envAnalysis.dependencyRiskScore ?? 0)" size="small" effect="plain">
                  {{ envAnalysis.dependencyRiskScore ?? 0 }}
                </el-tag>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="env-subscore-item">
                <span class="env-subscore-label">CUDA 风险分</span>
                <el-progress
                  :percentage="envAnalysis.cudaRiskScore ?? 0"
                  :color="riskScoreColor(envAnalysis.cudaRiskScore ?? 0)"
                  :stroke-width="10"
                />
                <el-tag :type="riskScoreType(envAnalysis.cudaRiskScore ?? 0)" size="small" effect="plain">
                  {{ envAnalysis.cudaRiskScore ?? 0 }}
                </el-tag>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="env-subscore-item">
                <span class="env-subscore-label">Docker 成熟度</span>
                <el-progress
                  :percentage="envAnalysis.dockerReadinessScore ?? 0"
                  :color="envScoreColor(envAnalysis.dockerReadinessScore ?? 0)"
                  :stroke-width="10"
                />
                <el-tag :type="dockerScoreType(envAnalysis.dockerReadinessScore ?? 0)" size="small" effect="plain">
                  {{ envAnalysis.dockerReadinessScore ?? 0 }}
                </el-tag>
              </div>
            </el-col>
          </el-row>

          <el-divider />

          <!-- 风险摘要 -->
          <div class="env-text-section">
            <h4>风险摘要</h4>
            <p>{{ envAnalysis.riskSummary || '暂无环境风险摘要。' }}</p>
          </div>

          <el-divider />

          <!-- 安装建议 -->
          <div class="env-text-section">
            <h4>安装建议</h4>
            <pre class="env-advice-box">{{ envAnalysis.installAdvice || '暂无安装建议。' }}</pre>
          </div>

          <el-divider />

          <!-- 依赖列表 -->
          <div class="env-deps-section">
            <h4>
              依赖列表
              <span class="env-deps-count">
                （共 {{ envDeps.length }} 条{{ envDeps.length > 50 ? ', 仅展示前 50 条' : '' }}）
              </span>
              <el-button size="small" text type="primary" @click="loadEnvironmentData" :icon="'Refresh'" style="margin-left: 8px">
                刷新
              </el-button>
            </h4>
            <el-table
              v-if="envDeps.length > 0"
              :data="envDeps.slice(0, 50)"
              border
              stripe
              size="small"
              max-height="400"
              style="width: 100%"
            >
              <el-table-column prop="packageName" label="包名" min-width="140" show-overflow-tooltip />
              <el-table-column prop="versionSpec" label="版本" min-width="100" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.versionSpec">{{ row.versionSpec }}</span>
                  <span v-else class="text-muted">未固定</span>
                </template>
              </el-table-column>
              <el-table-column prop="source" label="来源" width="80">
                <template #default="{ row }">
                  <el-tag size="small" type="info" effect="plain">{{ row.source || '-' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="filePath" label="文件" min-width="120" show-overflow-tooltip />
              <el-table-column prop="riskLevel" label="风险" width="70">
                <template #default="{ row }">
                  <el-tag
                    v-if="row.riskLevel"
                    size="small"
                    :type="depRiskTagType(row.riskLevel)"
                    effect="dark"
                  >{{ depRiskTagLabel(row.riskLevel) }}</el-tag>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="riskReason" label="风险原因" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.riskReason" class="env-risk-reason">{{ row.riskReason }}</span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
            </el-table>
            <div v-else class="text-muted" style="text-align:center; padding: 16px 0">暂无依赖数据</div>
          </div>
        </template>

        <!-- 环境分析错误 -->
        <el-alert v-if="envError" :title="envError" type="error" show-icon :closable="false" style="margin-top: 8px" />
      </el-card>

      <!-- 完整度检查区 -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon size="18"><List /></el-icon>
            <span>仓库文件完整度</span>
            <el-tag size="small" :type="completenessTagType" style="margin-left: auto">
              {{ completenessSummary }}
            </el-tag>
          </div>
        </template>
        <div class="checklist">
          <div v-for="item in analysisItems" :key="item.label" class="checklist-row">
            <el-icon :size="18" :color="item.value ? '#67c23a' : '#f56c6c'">
              <CircleCheckFilled v-if="item.value" />
              <CircleCloseFilled v-else />
            </el-icon>
            <span class="checklist-label">{{ item.label }}</span>
            <el-tag :type="item.value ? 'success' : 'danger'" size="small" effect="plain">
              {{ item.value ? '是' : '否' }}
            </el-tag>
            <!-- 匹配文件 -->
            <template v-if="item.value && matchedFiles(item.fileKey).length > 0">
              <span class="file-sep">—</span>
              <el-tag
                v-for="(f, fi) in matchedFiles(item.fileKey).slice(0, 5)"
                :key="fi"
                size="small"
                effect="plain"
                class="file-tag"
              >{{ f }}</el-tag>
              <el-tag v-if="matchedFiles(item.fileKey).length > 5" size="small" type="info" effect="plain">
                等 {{ matchedFiles(item.fileKey).length }} 个
              </el-tag>
            </template>
            <span v-else-if="item.value" class="text-muted" style="font-size:12px">未记录</span>
          </div>
        </div>
      </el-card>

      <!-- README 分析区 -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon size="18"><Reading /></el-icon>
            <span>README 文档分析</span>
            <el-tag
              size="small"
              style="margin-left: auto"
              :type="readmeQualityTagType"
            >评分 {{ report.repoAnalysis?.readmeQualityScore ?? '-' }}</el-tag>
          </div>
        </template>
        <template v-if="readmeAnalysisData">
          <div class="checklist">
            <div class="checklist-row">
              <el-icon :size="18" :color="readmeAnalysisData.hasInstallSection ? '#67c23a' : '#f56c6c'">
                <CircleCheckFilled v-if="readmeAnalysisData.hasInstallSection" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span class="checklist-label">安装说明</span>
              <el-tag :type="readmeAnalysisData.hasInstallSection ? 'success' : 'danger'" size="small" effect="plain">
                {{ readmeAnalysisData.hasInstallSection ? '是' : '否' }}
              </el-tag>
            </div>
            <div class="checklist-row">
              <el-icon :size="18" :color="readmeAnalysisData.hasTrainSection ? '#67c23a' : '#f56c6c'">
                <CircleCheckFilled v-if="readmeAnalysisData.hasTrainSection" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span class="checklist-label">训练说明</span>
              <el-tag :type="readmeAnalysisData.hasTrainSection ? 'success' : 'danger'" size="small" effect="plain">
                {{ readmeAnalysisData.hasTrainSection ? '是' : '否' }}
              </el-tag>
            </div>
            <div class="checklist-row">
              <el-icon :size="18" :color="readmeAnalysisData.hasInferenceSection ? '#67c23a' : '#f56c6c'">
                <CircleCheckFilled v-if="readmeAnalysisData.hasInferenceSection" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span class="checklist-label">推理说明</span>
              <el-tag :type="readmeAnalysisData.hasInferenceSection ? 'success' : 'danger'" size="small" effect="plain">
                {{ readmeAnalysisData.hasInferenceSection ? '是' : '否' }}
              </el-tag>
            </div>
            <div class="checklist-row">
              <el-icon :size="18" :color="readmeAnalysisData.hasDatasetSection ? '#67c23a' : '#f56c6c'">
                <CircleCheckFilled v-if="readmeAnalysisData.hasDatasetSection" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span class="checklist-label">数据集说明</span>
              <el-tag :type="readmeAnalysisData.hasDatasetSection ? 'success' : 'danger'" size="small" effect="plain">
                {{ readmeAnalysisData.hasDatasetSection ? '是' : '否' }}
              </el-tag>
            </div>
            <div class="checklist-row">
              <el-icon :size="18" :color="readmeAnalysisData.hasWeightSection ? '#67c23a' : '#f56c6c'">
                <CircleCheckFilled v-if="readmeAnalysisData.hasWeightSection" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span class="checklist-label">模型权重说明</span>
              <el-tag :type="readmeAnalysisData.hasWeightSection ? 'success' : 'danger'" size="small" effect="plain">
                {{ readmeAnalysisData.hasWeightSection ? '是' : '否' }}
              </el-tag>
            </div>
            <div class="checklist-row">
              <el-icon :size="18" :color="readmeAnalysisData.hasCitationSection ? '#67c23a' : '#f56c6c'">
                <CircleCheckFilled v-if="readmeAnalysisData.hasCitationSection" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span class="checklist-label">引用说明</span>
              <el-tag :type="readmeAnalysisData.hasCitationSection ? 'success' : 'danger'" size="small" effect="plain">
                {{ readmeAnalysisData.hasCitationSection ? '是' : '否' }}
              </el-tag>
            </div>
            <div class="checklist-row">
              <el-icon :size="18" :color="readmeAnalysisData.hasExampleCommands ? '#67c23a' : '#f56c6c'">
                <CircleCheckFilled v-if="readmeAnalysisData.hasExampleCommands" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span class="checklist-label">示例命令</span>
              <el-tag :type="readmeAnalysisData.hasExampleCommands ? 'success' : 'danger'" size="small" effect="plain">
                {{ readmeAnalysisData.hasExampleCommands ? '是' : '否' }}
              </el-tag>
            </div>
          </div>
          <el-divider />
          <div class="readme-meta">
            <span v-if="readmeAnalysisData.readmeLength">README 长度：{{ (readmeAnalysisData.readmeLength / 1000).toFixed(1) }} KB</span>
            <span v-else>README 长度：未知</span>
          </div>
        </template>
        <div v-else class="text-muted" style="text-align:center; padding: 16px 0">暂无 README 分析数据</div>
      </el-card>

      <!-- 分析总结区 -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon size="18"><Reading /></el-icon>
            <span>分析总结</span>
          </div>
        </template>
        <div class="text-section">
          <h4>总体评估</h4>
          <p>{{ report.report.summary || '暂无' }}</p>
        </div>
        <el-divider />
        <div class="text-section">
          <h4>核心方法</h4>
          <p>{{ report.report.methodSummary || '暂无' }}</p>
        </div>
        <el-divider />
        <div class="text-section">
          <h4>主要创新点</h4>
          <p>{{ report.report.innovationSummary || '暂无' }}</p>
        </div>
      </el-card>

      <!-- 复现步骤区 -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon size="18"><Operation /></el-icon>
            <span>建议复现步骤</span>
          </div>
        </template>
        <pre class="steps-box" v-if="report.report.reproduceSteps">{{ report.report.reproduceSteps }}</pre>
        <div v-else class="text-muted">暂无</div>
      </el-card>

      <!-- 风险提示区 -->
      <el-card class="section-card" :class="'risk-' + (report.report.riskLevel || '').toLowerCase()" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon size="18"><WarningFilled /></el-icon>
            <span>风险提示</span>
          </div>
        </template>
        <div class="risk-content" v-if="report.report.riskTips">{{ report.report.riskTips }}</div>
        <div v-else class="text-muted">暂无风险提示</div>
      </el-card>

      <!-- 最终建议区 -->
      <el-card class="section-card advice-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon size="18"><Medal /></el-icon>
            <span>最终建议</span>
          </div>
        </template>
        <div class="advice-content">
          {{ report.report.finalAdvice || fallbackAdvice(report.report.riskLevel) }}
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowDown, ArrowUp, CircleCheckFilled, CircleCloseFilled,
  Document, Download, FolderOpened, List, Loading, Medal,
  Operation, Reading, Refresh, Setting, WarningFilled,
} from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import { updateRepo } from '@/api/repo'
import { rebuildAnalysis } from '@/api/analysis'
import { exportMarkdownReport } from '@/api/report'
import { getEnvironmentAnalysis, getDependencies, rebuildEnvironmentAnalysis } from '@/api/environment'
import type { EnvironmentAnalysis, DependencyAnalysis } from '@/api/types'

const route = useRoute()
const taskStore = useTaskStore()
const loading = ref(false)
const loadError = ref('')
const manualRepoLoading = ref(false)
const exportLoading = ref(false)
const refreshLoading = ref(false)
const abstractExpanded = ref(false)
const manualRepoForm = ref({ url: '' })

// ── 环境分析状态 ──
const envAnalysis = ref<EnvironmentAnalysis | null>(null)
const envDeps = ref<DependencyAnalysis[]>([])
const envLoading = ref(false)
const envRebuildLoading = ref(false)
const envNotGenerated = ref(false)
const envError = ref('')

const task = computed(() => taskStore.currentTask)
const report = computed(() => taskStore.currentReport)

const analysisItems = computed(() => {
  if (!report.value) return []
  const a = report.value.repoAnalysis
  if (!a) return []
  return [
    { label: 'README.md', value: a.hasReadme, fileKey: 'readmeFiles' },
    { label: '依赖文件 (requirements/pyproject/setup)', value: a.hasRequirements, fileKey: 'dependencyFiles' },
    { label: 'Conda 环境文件 (environment.yml)', value: a.hasEnvironmentYml, fileKey: '' },
    { label: 'Dockerfile', value: a.hasDockerfile, fileKey: 'dockerFiles' },
    { label: 'LICENSE', value: a.hasLicense, fileKey: 'licenseFiles' },
    { label: '训练代码', value: a.hasTrainCode, fileKey: 'trainFiles' },
    { label: '推理/Demo 代码', value: a.hasInferenceCode, fileKey: 'inferenceFiles' },
    { label: '数据集说明', value: a.hasDatasetDoc, fileKey: 'datasetRelatedFiles' },
    { label: '模型权重说明', value: a.hasWeightDoc, fileKey: 'weightRelatedFiles' },
  ]
})

const completenessSummary = computed(() => {
  const items = analysisItems.value
  if (!items.length) return '未知'
  const yes = items.filter(i => i.value).length
  return `${yes}/${items.length} 项具备`
})

const completenessTagType = computed(() => {
  const items = analysisItems.value
  if (!items.length) return 'info'
  const yes = items.filter(i => i.value).length
  const ratio = yes / items.length
  if (ratio >= 0.7) return 'success'
  if (ratio >= 0.4) return 'warning'
  return 'danger'
})

function matchedFiles(fileKey: string): string[] {
  const fm = report.value?.repoAnalysis?.fileMatches
  if (!fm) return []
  const key = fileKey as keyof typeof fm
  return (fm[key] as string[]) || []
}

// README 分析
const readmeAnalysisData = computed(() => report.value?.repoAnalysis?.readmeAnalysis ?? null)

const readmeQualityTagType = computed(() => {
  const score = report.value?.repoAnalysis?.readmeQualityScore ?? 0
  if (score >= 70) return 'success'
  if (score >= 40) return 'warning'
  return 'danger'
})

onMounted(() => { loadData() })
onUnmounted(() => { taskStore.stopPolling() })
watch(() => route.params.id, () => { taskStore.stopPolling(); loadData() })

async function loadData() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  loadError.value = ''
  try {
    await taskStore.loadTaskDetail(id)
    await taskStore.loadTaskTimeline(id)

    const s = taskStore.currentTask?.status
    if (s === 'SUCCESS') {
      try { await taskStore.loadReport(id) } catch { /* 报告可能未生成 */ }
      loadEnvironmentData()
    } else if (s && !isTerminal(s)) {
      taskStore.startPolling(id)
    }
  } catch (e: any) {
    loadError.value = e?.message || '加载数据失败'
  } finally {
    loading.value = false
  }
}

async function loadEnvironmentData() {
  const id = Number(route.params.id)
  if (!id) return
  envLoading.value = true
  envNotGenerated.value = false
  envError.value = ''
  try {
    const [analysisRes, depsRes] = await Promise.all([
      getEnvironmentAnalysis(id),
      getDependencies(id),
    ])
    envAnalysis.value = analysisRes.data
    envDeps.value = depsRes.data || []
  } catch (e: any) {
    const msg = e?.message || ''
    if (msg.includes('尚未生成') || msg.includes('not found') || msg.includes('不存在')) {
      envNotGenerated.value = true
    } else {
      envError.value = msg
    }
  } finally {
    envLoading.value = false
  }
}

async function handleRebuildAnalysis() {
  const id = Number(route.params.id)
  if (!id) return
  envRebuildLoading.value = true
  envError.value = ''
  try {
    await rebuildEnvironmentAnalysis(id)
    ElMessage.success('环境分析完成')
    envNotGenerated.value = false
    await loadEnvironmentData()
  } catch (e: any) {
    ElMessage.error(e?.message || '环境分析失败')
  } finally {
    envRebuildLoading.value = false
  }
}

async function handleRefreshReport() {
  const id = Number(route.params.id)
  if (!id) return
  refreshLoading.value = true
  loadError.value = ''
  taskStore.currentReport = null
  try {
    await taskStore.loadTaskDetail(id)
    await taskStore.loadReport(id)
    ElMessage.success('报告已刷新')
  } catch (e: any) {
    loadError.value = e?.message || '刷新失败'
  } finally {
    refreshLoading.value = false
  }
}

function isTerminal(status: string): boolean {
  return status === 'SUCCESS' || status === 'FAILED' || status === 'CANCELLED'
}

async function handleRetry() {
  const id = Number(route.params.id)
  try {
    await taskStore.retry(id)
    ElMessage.success('任务已重新提交')
    taskStore.currentReport = null
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '重试失败')
  }
}

async function handleManualRepo() {
  const id = Number(route.params.id)
  const url = manualRepoForm.value.url.trim()
  if (!url) return
  if (!/^https?:\/\/github\.com\/[^/]+\/[^/]+/.test(url)) {
    ElMessage.warning('请输入合法的 GitHub 仓库链接，例如 https://github.com/owner/repo')
    return
  }
  manualRepoLoading.value = true
  taskStore.currentReport = null
  try {
    await updateRepo(id, { repoUrl: url, platform: 'GitHub' })
    await rebuildAnalysis(id)
    ElMessage.success('仓库分析完成')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '仓库分析失败')
  } finally {
    manualRepoLoading.value = false
  }
}

async function handleExportMarkdown() {
  const id = Number(route.params.id)
  if (!id) return
  exportLoading.value = true
  try {
    await exportMarkdownReport(id)
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '导出失败')
  } finally {
    exportLoading.value = false
  }
}

// ── 环境诊断辅助 ──

function envScoreType(score: number): string {
  if (score >= 75) return 'success'
  if (score >= 50) return 'warning'
  return 'danger'
}

function envScoreColor(score: number): string {
  if (score >= 75) return '#67c23a'
  if (score >= 50) return '#e6a23c'
  return '#f56c6c'
}

/** risk 分：越高越危险，颜色反转 */
function riskScoreType(score: number): string {
  if (score >= 70) return 'danger'
  if (score >= 40) return 'warning'
  return 'success'
}

function riskScoreColor(score: number): string {
  if (score >= 70) return '#f56c6c'
  if (score >= 40) return '#e6a23c'
  return '#67c23a'
}

/** Docker 分：越高越好 */
function dockerScoreType(score: number): string {
  if (score >= 75) return 'success'
  if (score >= 50) return 'warning'
  return 'danger'
}

function depRiskTagType(level: string): string {
  const map: Record<string, string> = { HIGH: 'danger', MEDIUM: 'warning', LOW: 'success' }
  return map[level] || 'info'
}

function depRiskTagLabel(level: string): string {
  const map: Record<string, string> = { HIGH: '高', MEDIUM: '中', LOW: '低' }
  return map[level] || level || '-'
}

// ── 辅助方法 ──

function fallbackAdvice(level: string): string {
  const map: Record<string, string> = {
    LOW: '该论文代码仓库完整，环境友好，推荐尝试复现。',
    MEDIUM: '仓库中存在部分缺失，建议谨慎评估复现成本后再决定。',
    HIGH: '仓库完整度较低或环境复杂度过高，不建议直接投入大量时间复现。',
  }
  return map[level] || '暂无建议'
}

function riskLabel(level: string): string {
  const map: Record<string, string> = { LOW: '低风险', MEDIUM: '中等风险', HIGH: '高风险' }
  return map[level] || level || '未知'
}

function riskTagType(level: string): string {
  const map: Record<string, string> = { LOW: 'success', MEDIUM: 'warning', HIGH: 'danger' }
  return map[level] || 'info'
}

function scoreColor(score: number): string {
  if (score >= 75) return '#67c23a'
  if (score >= 50) return '#e6a23c'
  return '#f56c6c'
}

function statusType(status: string): string {
  const map: Record<string, string> = {
    PENDING: 'info', PARSING_PAPER: 'warning', SEARCHING_REPO: 'warning',
    ANALYZING_REPO: 'warning', GENERATING_REPORT: 'warning',
    SUCCESS: 'success', FAILED: 'danger', CANCELLED: 'info',
  }
  return map[status] || 'info'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    PENDING: '等待中', PARSING_PAPER: '解析论文中', SEARCHING_REPO: '搜索仓库中',
    ANALYZING_REPO: '分析仓库中', GENERATING_REPORT: '生成报告中',
    SUCCESS: '已完成', FAILED: '失败', CANCELLED: '已取消',
  }
  return map[status] || status
}

function timelineColor(status: string): string {
  const map: Record<string, string> = {
    PENDING: '#409eff', PARSING_PAPER: '#e6a23c', SEARCHING_REPO: '#e6a23c',
    ANALYZING_REPO: '#e6a23c', GENERATING_REPORT: '#e6a23c',
    SUCCESS: '#67c23a', FAILED: '#f56c6c', CANCELLED: '#909399',
  }
  return map[status] || '#909399'
}
</script>

<style scoped>
/* ── 页面容器 ── */
.task-detail-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}

/* ── 顶部概览区 ── */
.page-header {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.header-left {
  flex-shrink: 0;
  padding-top: 2px;
}

.header-center {
  flex: 1;
  min-width: 0;
}

.paper-title {
  margin: 0 0 10px;
  font-size: 18px;
  color: #303133;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.header-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.score-inline {
  font-size: 14px;
  font-weight: 600;
  margin-left: 4px;
}

.header-right {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* ── 卡片通用 ── */
.info-card {
  margin-bottom: 16px;
}

.section-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #303133;
}

/* ── 评分卡片 ── */
.score-row {
  margin-bottom: 4px;
}

.score-card :deep(.el-card__body) {
  padding: 24px 12px;
}

.score-card-inner {
  text-align: center;
}

.score-number {
  font-size: 32px;
  font-weight: 700;
}

.score-title {
  margin-top: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.score-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

/* ── 论文摘要 ── */
.abstract-section {
  margin-top: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.abstract-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  background: #fafafa;
  user-select: none;
  border-radius: 4px;
}
.abstract-toggle:hover { background: #f0f2f5; }

.abstract-content {
  padding: 16px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 14px;
  max-height: 200px;
  overflow-y: auto;
}

/* ── 仓库信息 ── */
.confidence-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.confidence-text {
  font-size: 12px;
  color: #909399;
}

.empty-state {
  text-align: center;
  padding: 8px 0;
}

.empty-tip {
  color: #909399;
  font-size: 13px;
  margin-top: -8px;
}

/* ── 文件完整度检查 ── */
.checklist {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px 16px;
}

.checklist-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 8px;
  padding: 10px 12px;
  border-radius: 4px;
  background: #fafafa;
  font-size: 14px;
}

.checklist-label {
  flex: 1;
  color: #606266;
}

.file-sep {
  color: #c0c4cc;
  margin: 0 4px;
  font-size: 12px;
}

.file-tag {
  margin-right: 4px;
  font-size: 11px;
}

/* ── AI 分析文本 ── */
.text-section h4 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #303133;
}

.text-section p {
  margin: 0;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* ── 复现步骤 ── */
.steps-box {
  background: #f5f7fa;
  padding: 16px 20px;
  border-radius: 6px;
  color: #4a4d52;
  line-height: 1.9;
  white-space: pre-wrap;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  margin: 0;
  overflow-x: auto;
}

/* ── 风险提示 - 按等级配色 ── */
.risk-low   :deep(.el-card__body) { background: #f0f9eb; border-left: 4px solid #67c23a; }
.risk-medium:deep(.el-card__body) { background: #fdf6ec; border-left: 4px solid #e6a23c; }
.risk-high  :deep(.el-card__body) { background: #fef0f0; border-left: 4px solid #f56c6c; }

.risk-content {
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 14px;
}

/* ── 最终建议 ── */
.advice-card :deep(.el-card__body) {
  border-left: 4px solid #409eff;
  background: #ecf5ff;
}

.advice-content {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* ── 分析中提示 ── */
.analyzing-hint {
  text-align: center;
  padding: 24px;
}

.analyzing-hint p {
  margin: 8px 0 0;
  color: #606266;
  font-size: 15px;
}

.hint-sub {
  font-size: 13px !important;
  color: #909399 !important;
}

/* ── 通用 ── */
.text-muted {
  color: #909399;
  font-style: italic;
}

/* ── V2.0 环境诊断 ── */
.env-empty {
  padding: 8px 0;
}

.env-metrics-row {
  margin-bottom: 12px;
}

.env-metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 8px 4px;
  background: #fafafa;
  border-radius: 6px;
  min-height: 110px;
  justify-content: center;
}

.env-metric-label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.env-metric-value {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  word-break: break-all;
  text-align: center;
}

.env-metric-sub {
  font-size: 12px;
  color: #909399;
}

.env-metric-small {
  font-size: 12px !important;
  font-weight: 400 !important;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.env-metric-score {
  font-size: 20px;
  font-weight: 700;
}

.env-subscores-row {
  margin-bottom: 4px;
}

.env-subscore-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 12px;
}

.env-subscore-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.env-text-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #303133;
}

.env-text-section p {
  margin: 0;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
}

.env-advice-box {
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 6px;
  color: #4a4d52;
  line-height: 1.9;
  white-space: pre-wrap;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  margin: 0;
  overflow-x: auto;
}

.env-deps-section h4 {
  margin: 0 0 10px;
  font-size: 14px;
  color: #303133;
  display: flex;
  align-items: center;
}

.env-deps-count {
  font-weight: 400;
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}

.env-risk-reason {
  font-size: 12px;
  color: #606266;
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .task-detail-page { padding: 12px 8px 24px; }
  .page-header { flex-wrap: wrap; }
  .header-right { margin-left: 0; }
  .checklist { grid-template-columns: repeat(2, 1fr); }
  .score-row .el-col { margin-bottom: 12px; }
}
</style>
