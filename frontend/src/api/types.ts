// ---------- 通用类型 ----------

/** 后端统一响应包装 */
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// ---------- 请求类型 ----------

export interface CreateTaskReq {
  paperUrl: string
}

/** 任务列表查询参数 */
export interface TaskQueryParams {
  page?: number
  size?: number
  status?: string
  keyword?: string
  startTime?: string
  endTime?: string
  sortField?: string
  sortOrder?: 'asc' | 'desc'
}

export interface BatchDeleteTaskReq {
  taskIds: number[]
}

export interface BatchDeleteResultItem {
  taskId: number
  success: boolean
  message: string
}

export type BatchDeleteTaskRes = ApiResponse<{
  successCount: number
  failedCount: number
  results: BatchDeleteResultItem[]
}>

export interface BatchExportMarkdownReq {
  taskIds: number[]
}

// ---------- 响应类型 ----------

export type CreateTaskRes = ApiResponse<{
  taskId: number
}>

export interface TaskItem {
  id: number
  paperTitle: string
  paperUrl: string
  status: string
  errorMessage: string | null
  createTime: string
  updateTime: string
  finishTime: string | null
}

export interface PageResult<T> {
  records: T[]
  total: number
  page: number
  size: number
}

export type TaskListRes = ApiResponse<PageResult<TaskItem>>

export interface TaskDetail {
  id: number
  userId: number
  paperUrl: string
  paperTitle: string
  status: string
  errorMessage: string | null
  createTime: string
  updateTime: string
  finishTime: string | null
}

export interface PaperInfo {
  arxivId: string
  title: string
  authors: string
  abstractText: string
  publishedAt: string
  paperUrl: string
}

export interface RepoInfo {
  platform: string
  repoUrl: string
  repoName: string
  owner: string
  stars: number
  forks: number
  defaultBranch: string
  lastUpdatedAt: string
  confidence: number
  confidenceReason: string
}

export interface RepoAnalysis {
  hasReadme: boolean
  hasRequirements: boolean
  hasEnvironmentYml: boolean
  hasDockerfile: boolean
  hasLicense: boolean
  hasTrainCode: boolean
  hasInferenceCode: boolean
  hasDatasetDoc: boolean
  hasWeightDoc: boolean
  readmeQualityScore: number
  dependencyComplexityScore: number
  structureCompletenessScore: number
  fileMatches?: {
    readmeFiles?: string[]
    dependencyFiles?: string[]
    dockerFiles?: string[]
    licenseFiles?: string[]
    trainFiles?: string[]
    inferenceFiles?: string[]
    datasetRelatedFiles?: string[]
    weightRelatedFiles?: string[]
  }
  readmeAnalysis?: {
    hasInstallSection?: boolean
    hasTrainSection?: boolean
    hasInferenceSection?: boolean
    hasDatasetSection?: boolean
    hasWeightSection?: boolean
    hasCitationSection?: boolean
    hasExampleCommands?: boolean
    readmeLength?: number
  }
}

export interface ReportData {
  reproducibilityScore: number
  completenessScore: number
  environmentScore: number
  riskLevel: string
  summary: string
  methodSummary: string
  innovationSummary: string
  reproduceSteps: string
  riskTips: string
  finalAdvice?: string
}

export interface ReportDetail {
  paperInfo: PaperInfo
  repoInfo: RepoInfo
  repoAnalysis: RepoAnalysis
  report: ReportData
}

// ---------- 新增 V1.0 类型 ----------

export interface TaskStatusItem {
  taskId: number
  status: string
  message: string
  errorMessage: string | null
  finished: boolean
  finishTime: string | null
}

export interface TaskTimelineItem {
  id: number
  taskId: number
  status: string
  message: string
  createTime: string
}

export interface TaskTimeline {
  taskId: number
  timeline: TaskTimelineItem[]
}

export interface RepoCandidateItem {
  platform: string
  repoUrl: string
  repoName: string
  owner: string
  stars: number
  forks: number
  defaultBranch: string
  lastUpdatedAt: string
  confidence: number
  confidenceReason: string
}

export interface RepoCandidateList {
  selectedIndex: number
  candidates: RepoCandidateItem[]
}

export interface ReadmeAnalysis {
  hasInstallSection: boolean
  hasTrainSection: boolean
  hasInferenceSection: boolean
  hasDatasetSection: boolean
  hasWeightSection: boolean
  hasCitationSection: boolean
  hasExampleCommands: boolean
  readmeLength: number
  readmeQualityScore: number
}

export interface ReportScores {
  reproducibilityScore: number
  completenessScore: number
  environmentScore: number
  riskLevel: string
}

export interface SystemHealth {
  status: string
  mysql: string
  redis: string
  minio: string
}

export interface AiHealth {
  aiServiceStatus: string
  aiServiceUrl: string
}

export interface SystemConfig {
  appName: string
  version: string
  maxTaskPerUser: number
  supportedPlatforms: string[]
}

export interface FileUploadItem {
  fileId: string
  fileName: string
  fileSize: number
}

export interface FileDownloadItem {
  downloadUrl: string
  expireAt: string
}

// Auth 类型
export interface LoginReq { username: string; password: string }
export interface RegisterReq { username: string; password: string; email?: string }
export interface LoginRes { token: string; userId: number; username: string; email?: string }
export interface CurrentUser { id: number; username: string; email: string; createTime: string }

// User 类型
export interface UpdateUserReq { email?: string }
export interface UpdatePasswordReq { oldPassword: string; newPassword: string }
export interface UserInfo { id: number; username: string; email: string; createTime: string }

// Repo 更新类型
export interface UpdateRepoReq { repoUrl: string; platform: string }

// ═══════════════════════════════════════════════
// V2.0 环境分析
// ═══════════════════════════════════════════════

export interface DependencyAnalysis {
  id: number
  taskId: number
  fileType: string
  filePath: string
  packageName: string
  versionSpec: string | null
  source: string | null
  riskLevel: string | null
  riskReason: string | null
}

export interface EnvironmentAnalysis {
  taskId: number
  pythonVersion: string | null
  cudaVersion: string | null
  mainFramework: string | null
  frameworkVersion: string | null
  requiresGpu: boolean
  hasDocker: boolean
  dockerBaseImage: string | null
  dependencyRiskScore: number
  cudaRiskScore: number
  dockerReadinessScore: number
  environmentScore: number
  riskLevel: string
  riskSummary: string | null
  installAdvice: string | null
}

export interface EnvironmentReport {
  taskId: number
  environmentAnalysis: EnvironmentAnalysis
  dependencies: DependencyAnalysis[]
}

export type TaskDetailRes = ApiResponse<TaskDetail>
export type ReportDetailRes = ApiResponse<ReportDetail>
export type TaskStatusRes = ApiResponse<TaskStatusItem>
export type TaskTimelineRes = ApiResponse<TaskTimeline>
export type RepoInfoRes = ApiResponse<RepoInfo>
export type RepoCandidateRes = ApiResponse<RepoCandidateList>
export type RepoAnalysisRes = ApiResponse<RepoAnalysis>
export type ReadmeRes = ApiResponse<ReadmeAnalysis>
export type ReportScoresRes = ApiResponse<ReportScores>
export type SystemHealthRes = ApiResponse<SystemHealth>
export type AiHealthRes = ApiResponse<AiHealth>
export type SystemConfigRes = ApiResponse<SystemConfig>
export type FileUploadRes = ApiResponse<FileUploadItem>
export type FileDownloadRes = ApiResponse<FileDownloadItem>
export type LoginResWrapped = ApiResponse<LoginRes>
export type CurrentUserRes = ApiResponse<CurrentUser>
export type UserInfoRes = ApiResponse<UserInfo>

// V2.0 环境分析响应类型
export type EnvironmentAnalysisRes = ApiResponse<EnvironmentAnalysis>
export type DependencyListRes = ApiResponse<DependencyAnalysis[]>
export type EnvironmentReportRes = ApiResponse<EnvironmentReport>
