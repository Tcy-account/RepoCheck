<template>
  <div class="home-page">
    <div class="hero">
      <h1 class="hero-title">RepoCheck</h1>
      <p class="hero-desc">论文代码可用性检测器 — 输入 arXiv 论文链接，自动分析仓库质量，生成复现可行性报告</p>
    </div>

    <el-card class="submit-card" shadow="hover">
      <h3>提交检测任务</h3>
      <div class="submit-form">
        <el-input
          v-model="paperUrl"
          placeholder="输入 arXiv 论文链接，例如 https://arxiv.org/abs/2501.xxxxx"
          size="large"
          clearable
          @keyup.enter="handleSubmit"
        >
          <template #prefix>
            <el-icon><Link /></el-icon>
          </template>
        </el-input>
        <el-button
          type="primary"
          size="large"
          :loading="submitting"
          :disabled="!paperUrl.trim()"
          @click="handleSubmit"
        >
          开始检测
        </el-button>
      </div>
    </el-card>

    <el-card class="feature-card" shadow="hover">
      <h3>V1.0 功能特性</h3>
      <el-row :gutter="24">
        <el-col :span="8" v-for="feature in features" :key="feature.title">
          <div class="feature-item">
            <el-icon :size="32" color="#409eff">
              <component :is="feature.icon" />
            </el-icon>
            <h4>{{ feature.title }}</h4>
            <p>{{ feature.desc }}</p>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/task'

const router = useRouter()
const taskStore = useTaskStore()

const paperUrl = ref('')
const submitting = ref(false)

const features = [
  {
    icon: 'Document',
    title: '论文解析',
    desc: '自动解析 arXiv 论文元信息，包括标题、作者、摘要',
  },
  {
    icon: 'Search',
    title: '仓库发现',
    desc: '在 GitHub/GitLab 自动搜索对应的官方代码仓库',
  },
  {
    icon: 'DataAnalysis',
    title: '静态分析',
    desc: '分析仓库结构、依赖、文档完整性，生成复现评分',
  },
]

async function handleSubmit() {
  if (!paperUrl.value.trim()) return
  submitting.value = true
  try {
    const taskId = await taskStore.submitTask(paperUrl.value.trim())
    ElMessage.success('任务创建成功')
    router.push(`/tasks/${taskId}`)
  } catch (e: any) {
    ElMessage.error(e?.message || '任务创建失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.home-page {
  max-width: 800px;
  margin: 0 auto;
}

.hero {
  text-align: center;
  padding: 40px 0 32px;
}

.hero-title {
  font-size: 42px;
  font-weight: 800;
  color: #303133;
  margin: 0 0 16px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 16px;
  color: #909399;
  margin: 0;
  line-height: 1.6;
}

.submit-card {
  margin-bottom: 24px;
}

.submit-card h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #303133;
}

.submit-form {
  display: flex;
  gap: 12px;
}

.submit-form .el-input {
  flex: 1;
}

.feature-card h3 {
  margin: 0 0 20px;
  font-size: 16px;
  color: #303133;
}

.feature-item {
  text-align: center;
  padding: 16px 0;
}

.feature-item h4 {
  margin: 12px 0 8px;
  color: #303133;
}

.feature-item p {
  color: #909399;
  font-size: 13px;
  margin: 0;
}
</style>
