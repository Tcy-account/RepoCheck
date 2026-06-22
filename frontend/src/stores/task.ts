import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createTask, getTaskList, getTaskDetail, getReport, retryTask, getTaskStatus, getTaskTimeline } from '@/api/task'
import type { TaskItem, TaskDetail, ReportDetail, TaskStatusItem, TaskTimelineItem, TaskQueryParams } from '@/api/types'

export const useTaskStore = defineStore('task', () => {
  // 任务列表
  const tasks = ref<TaskItem[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(10)
  const loading = ref(false)

  // 当前筛选条件
  const currentFilters = ref<TaskQueryParams>({})

  // 当前任务详情
  const currentTask = ref<TaskDetail | null>(null)

  // 当前报告
  const currentReport = ref<ReportDetail | null>(null)

  // 当前任务状态 (用于轮询)
  const currentStatus = ref<TaskStatusItem | null>(null)

  // 当前时间线
  const currentTimeline = ref<TaskTimelineItem[]>([])

  // 轮询 ID
  let pollingTimer: ReturnType<typeof setInterval> | null = null

  /** 创建任务 */
  async function submitTask(paperUrl: string): Promise<number> {
    const res = await createTask({ paperUrl })
    return res.data.taskId
  }

  /** 加载任务列表（支持筛选参数） */
  async function loadTasks(page = 1, size?: number, filters?: TaskQueryParams) {
    loading.value = true
    // 保存筛选条件
    if (filters !== undefined) {
      currentFilters.value = { ...filters }
    }
    const effectiveSize = size ?? pageSize.value

    try {
      const params: TaskQueryParams = {
        page,
        size: effectiveSize,
        ...currentFilters.value,
      }
      // 清理空字符串
      if (!params.status) delete params.status
      if (!params.keyword) delete params.keyword

      const res = await getTaskList(params)
      tasks.value = res.data.records
      total.value = res.data.total
      currentPage.value = page
      pageSize.value = effectiveSize
    } finally {
      loading.value = false
    }
  }

  /** 清空筛选条件并重新加载 */
  async function resetAndLoad() {
    currentFilters.value = {}
    await loadTasks(1)
  }

  /** 加载任务详情 */
  async function loadTaskDetail(id: number) {
    const res = await getTaskDetail(id)
    currentTask.value = res.data
  }

  /** 加载报告 */
  async function loadReport(taskId: number) {
    const res = await getReport(taskId)
    currentReport.value = res.data
  }

  /** 加载任务状态 */
  async function loadTaskStatus(id: number) {
    const res = await getTaskStatus(id)
    currentStatus.value = res.data
  }

  /** 加载时间线 */
  async function loadTaskTimeline(id: number) {
    const res = await getTaskTimeline(id)
    currentTimeline.value = res.data.timeline || []
  }

  /** 重试任务 */
  async function retry(id: number) {
    await retryTask(id)
  }

  /** 开始轮询 */
  function startPolling(taskId: number) {
    stopPolling()
    pollingTimer = setInterval(async () => {
      try {
        await loadTaskStatus(taskId)
        await loadTaskTimeline(taskId)
        if (currentStatus.value && currentTask.value) {
          currentTask.value.status = currentStatus.value.status
          currentTask.value.errorMessage = currentStatus.value.errorMessage
          currentTask.value.finishTime = currentStatus.value.finishTime
        }
        if (currentStatus.value?.finished) {
          stopPolling()
          if (currentStatus.value.status === 'SUCCESS') {
            await loadTaskDetail(taskId)
            try {
              await loadReport(taskId)
            } catch {
              // 报告可能尚未生成
            }
          }
        }
      } catch {
        // 轮询失败不弹错误
      }
    }, 2000)
  }

  /** 停止轮询 */
  function stopPolling() {
    if (pollingTimer) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  return {
    tasks,
    total,
    currentPage,
    pageSize,
    loading,
    currentFilters,
    currentTask,
    currentReport,
    currentStatus,
    currentTimeline,
    submitTask,
    loadTasks,
    resetAndLoad,
    loadTaskDetail,
    loadReport,
    loadTaskStatus,
    loadTaskTimeline,
    retry,
    startPolling,
    stopPolling,
  }
})
