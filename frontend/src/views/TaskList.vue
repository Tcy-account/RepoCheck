<template>
  <div class="task-list-page">
    <div class="page-header">
      <h3>任务列表</h3>
    </div>

    <!-- 筛选栏 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索论文标题或链接"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="filterForm.status"
            placeholder="全部"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="s in statusOptions"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 260px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 批量操作工具栏 -->
    <div class="batch-toolbar" v-if="selectedIds.length > 0">
      <span class="selected-count">已选择 {{ selectedIds.length }} 个任务</span>
      <el-button type="danger" plain @click="handleBatchDelete">
        批量删除
      </el-button>
      <el-button type="primary" plain @click="handleBatchExport">
        批量导出 Markdown
      </el-button>
    </div>

    <!-- 表格 -->
    <el-card shadow="hover">
      <el-table
        ref="tableRef"
        :data="taskStore.tasks"
        v-loading="taskStore.loading"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="任务 ID" width="80" />
        <el-table-column prop="paperTitle" label="论文标题" min-width="260" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="140">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 6px">
              <el-tag :type="statusColor(row.status)" size="small">
                {{ statusLabel(row.status) }}
              </el-tag>
              <el-tooltip
                v-if="row.status === 'FAILED' && row.errorMessage"
                :content="row.errorMessage"
                placement="top"
              >
                <el-icon color="#f56c6c" style="cursor: pointer"><WarningFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column prop="finishTime" label="完成时间" width="180">
          <template #default="{ row }">
            <span v-if="row.finishTime">{{ row.finishTime }}</span>
            <span v-else style="color: #c0c4cc">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :disabled="row.status !== 'SUCCESS'"
              @click="$router.push(`/tasks/${row.id}`)"
            >
              查看报告
            </el-button>
            <el-button
              v-if="row.status === 'FAILED'"
              type="warning"
              link
              @click="handleRetry(row.id)"
            >
              重试
            </el-button>
            <el-tooltip
              v-if="!isTerminal(row.status)"
              content="任务正在分析中，请取消后再删除"
              placement="top"
            >
              <el-button type="danger" link disabled>删除</el-button>
            </el-tooltip>
            <el-button
              v-else
              type="danger"
              link
              @click="handleDelete(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="taskStore.currentPage"
          :page-size="taskStore.pageSize"
          :total="taskStore.total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { WarningFilled } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import { deleteTask, batchDeleteTasks } from '@/api/task'
import { batchExportMarkdownReports } from '@/api/report'
import type { TaskQueryParams, TaskItem, BatchDeleteTaskReq } from '@/api/types'
import type { ElTable } from 'element-plus'

const taskStore = useTaskStore()

const tableRef = ref<InstanceType<typeof ElTable>>()
const selectedIds = ref<number[]>([])

const filterForm = reactive({
  keyword: '',
  status: '',
})

const dateRange = ref<[string, string] | null>(null)

const statusOptions = [
  { value: 'PENDING', label: '等待中' },
  { value: 'PARSING_PAPER', label: '解析论文中' },
  { value: 'SEARCHING_REPO', label: '搜索仓库中' },
  { value: 'ANALYZING_REPO', label: '分析仓库中' },
  { value: 'GENERATING_REPORT', label: '生成报告中' },
  { value: 'SUCCESS', label: '已完成' },
  { value: 'FAILED', label: '失败' },
  { value: 'CANCELLED', label: '已取消' },
]

onMounted(() => {
  taskStore.loadTasks()
})

function handleSelectionChange(rows: TaskItem[]) {
  selectedIds.value = rows.map((r) => r.id)
}

function buildFilters(): TaskQueryParams {
  const f: TaskQueryParams = {}
  if (filterForm.keyword.trim()) f.keyword = filterForm.keyword.trim()
  if (filterForm.status) f.status = filterForm.status
  if (dateRange.value && dateRange.value.length === 2) {
    f.startTime = dateRange.value[0] + 'T00:00:00'
    f.endTime = dateRange.value[1] + 'T23:59:59'
  }
  return f
}

function handleSearch() {
  taskStore.loadTasks(1, undefined, buildFilters())
}

function handleReset() {
  filterForm.keyword = ''
  filterForm.status = ''
  dateRange.value = null
  taskStore.resetAndLoad()
}

function handlePageChange(page: number) {
  taskStore.loadTasks(page)
}

async function handleRetry(taskId: number) {
  try {
    await taskStore.retry(taskId)
    ElMessage.success('任务已重新提交')
    taskStore.loadTasks()
  } catch (e: any) {
    ElMessage.error(e?.message || '重试失败')
  }
}

function isTerminal(status: string): boolean {
  return ['SUCCESS', 'FAILED', 'CANCELLED'].includes(status)
}

async function handleDelete(taskId: number) {
  try {
    await ElMessageBox.confirm(
      '确认删除该任务吗？删除后不会在任务列表中显示。',
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await deleteTask(taskId)
    ElMessage.success('任务已删除')
    taskStore.loadTasks()
  } catch (e: any) {
    // 取消对话框不提示，其他显示
    if (e !== 'cancel' && e?.message) {
      ElMessage.error(e.message)
    }
  }
}

/** 批量删除 */
async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${selectedIds.value.length} 个任务吗？`,
      '批量删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    const data: BatchDeleteTaskReq = { taskIds: selectedIds.value }
    const res = await batchDeleteTasks(data)
    const { successCount, failedCount, results } = res.data

    if (failedCount > 0) {
      const failedMsgs = results
        .filter((r) => !r.success)
        .map((r) => `任务 ${r.taskId}: ${r.message}`)
        .join('\n')
      ElMessage.warning(`成功删除 ${successCount} 个，${failedCount} 个失败:\n${failedMsgs}`)
    } else {
      ElMessage.success(`成功删除 ${successCount} 个任务`)
    }
    selectedIds.value = []
    taskStore.loadTasks()
  } catch {
    // 取消
  }
}

/** 批量导出 Markdown */
let batchExportLoading = false
async function handleBatchExport() {
  if (selectedIds.value.length === 0 || batchExportLoading) return
  batchExportLoading = true
  try {
    ElMessage.info('正在生成批量报告...')
    await batchExportMarkdownReports({ taskIds: selectedIds.value })
    ElMessage.success('批量导出成功')
    selectedIds.value = []
  } catch (e: any) {
    ElMessage.error(e?.message || '批量导出失败')
  } finally {
    batchExportLoading = false
  }
}

function statusColor(status: string): 'success' | 'danger' | 'warning' | 'info' | '' {
  const map: Record<string, 'success' | 'danger' | 'warning' | 'info' | ''> = {
    PENDING: 'info',
    PARSING_PAPER: '',
    SEARCHING_REPO: 'warning',
    ANALYZING_REPO: 'warning',
    GENERATING_REPORT: '',
    SUCCESS: 'success',
    FAILED: 'danger',
    CANCELLED: 'info',
  }
  return map[status] || 'info'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    PENDING: '等待中',
    PARSING_PAPER: '解析论文中',
    SEARCHING_REPO: '搜索仓库中',
    ANALYZING_REPO: '分析仓库中',
    GENERATING_REPORT: '生成报告中',
    SUCCESS: '已完成',
    FAILED: '失败',
    CANCELLED: '已取消',
  }
  return map[status] || status
}
</script>

<style scoped>
.page-header {
  margin-bottom: 16px;
}

.page-header h3 {
  margin: 0;
  color: #303133;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.filter-form .el-form-item {
  margin-bottom: 0;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  margin-bottom: 12px;
  background: #ecf5ff;
  border-radius: 4px;
}

.selected-count {
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
  margin-right: 8px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
