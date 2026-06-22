/**
 * Mock 数据 —— 仅用于前端开发阶段独立调试
 * 真实环境对接后端 API 后，可删除此文件
 */

import type { ReportDetail, TaskItem, TaskDetail } from '@/api/types'

export const mockTaskList: TaskItem[] = [
  {
    id: 1,
    paperTitle: 'Sample Paper: A Novel Approach to Deep Learning',
    paperUrl: 'https://arxiv.org/abs/2501.00001',
    status: 'SUCCESS',
    createTime: '2025-01-15T10:00:00',
    finishTime: '2025-01-15T10:05:00',
  },
  {
    id: 2,
    paperTitle: 'Another Great Paper About Transformers',
    paperUrl: 'https://arxiv.org/abs/2501.00002',
    status: 'PENDING',
    createTime: '2025-01-15T11:00:00',
    finishTime: null,
  },
]

export const mockTaskDetail: TaskDetail = {
  id: 1,
  userId: 1,
  paperUrl: 'https://arxiv.org/abs/2501.00001',
  paperTitle: 'Sample Paper: A Novel Approach to Deep Learning',
  status: 'SUCCESS',
  errorMessage: null,
  createTime: '2025-01-15T10:00:00',
  updateTime: '2025-01-15T10:05:00',
  finishTime: '2025-01-15T10:05:00',
}

export const mockReport: ReportDetail = {
  paperInfo: {
    arxivId: '2501.00001',
    title: 'Sample Paper: A Novel Approach to Deep Learning',
    authors: 'John Doe, Jane Smith',
    abstractText: 'This paper proposes a novel approach to deep learning that achieves state-of-the-art results on multiple benchmarks. The method combines transformer architectures with graph neural networks to capture both sequential and structural information.',
    publishedAt: '2025-01-15',
    paperUrl: 'https://arxiv.org/abs/2501.00001',
  },
  repoInfo: {
    platform: 'GitHub',
    repoUrl: 'https://github.com/johndoe/sample-paper',
    repoName: 'sample-paper',
    owner: 'johndoe',
    stars: 128,
    forks: 32,
    defaultBranch: 'main',
    lastUpdatedAt: '2025-01-10T00:00:00',
    confidence: 0.95,
    confidenceReason: 'Repository link found on paper page',
  },
  repoAnalysis: {
    hasReadme: true,
    hasRequirements: true,
    hasEnvironmentYml: false,
    hasDockerfile: true,
    hasLicense: true,
    hasTrainCode: true,
    hasInferenceCode: true,
    hasDatasetDoc: false,
    hasWeightDoc: false,
    readmeQualityScore: 80,
    dependencyComplexityScore: 60,
    structureCompletenessScore: 75,
  },
  report: {
    reproducibilityScore: 70,
    completenessScore: 75,
    environmentScore: 60,
    riskLevel: 'MEDIUM',
    summary: '该论文提供了较为完整的代码仓库，包含训练和推理代码，README 质量较高。但缺少数据集说明和预训练模型权重说明，需要用户自行准备数据和训练。',
    methodSummary: '本文提出了一种结合 Transformer 和图神经网络的新方法，通过捕捉序列和结构信息实现更优的性能表现。',
    innovationSummary: '1. 首次将 Transformer 与 GNN 结合用于该任务\n2. 提出新的注意力机制\n3. 在多个基准数据集上达到 SOTA',
    reproduceSteps: '1. 安装依赖：pip install -r requirements.txt\n2. 准备数据集（需自行下载）\n3. 运行训练：python train.py\n4. 运行推理：python infer.py',
    riskTips: '注意：1. 缺少数据集下载说明\n2. 未提供预训练模型权重\n3. 环境配置可能较复杂，建议使用 Docker',
    finalAdvice: '建议优先使用 Docker 环境复现，并联系作者获取预训练权重。',
  },
}
