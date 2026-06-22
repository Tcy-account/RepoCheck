<template>
  <div class="profile-page">
    <el-card shadow="hover">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>个人中心</span>
          <el-button type="danger" plain size="small" @click="handleLogout">退出登录</el-button>
        </div>
      </template>
      <el-descriptions v-if="userStore.user" :column="2" border>
        <el-descriptions-item label="用户 ID">{{ userStore.user.id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ userStore.user.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ userStore.user.email || '-' }}</el-descriptions-item>
      </el-descriptions>
      <div v-else style="text-align: center; padding: 24px; color: #909399">未登录</div>
    </el-card>

    <el-card shadow="hover" style="margin-top: 16px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>历史任务</span>
          <el-button type="primary" link @click="$router.push('/tasks')">查看全部</el-button>
        </div>
      </template>
      <el-empty v-if="taskStore.tasks.length === 0" description="暂无任务" />
      <el-table v-else :data="taskStore.tasks.slice(0, 5)" stripe>
        <el-table-column prop="id" label="任务 ID" width="100" />
        <el-table-column prop="paperTitle" label="论文标题" min-width="300" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useTaskStore } from '@/stores/task'
import { logout } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()
const taskStore = useTaskStore()

onMounted(async () => {
  await userStore.fetchUser()
  taskStore.loadTasks()
})

async function handleLogout() {
  try {
    await logout()
  } catch {
    // 即使接口失败也清除本地状态
  }
  userStore.clearAuth()
  ElMessage.success('已退出登录')
  router.push('/login')
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
</script>
