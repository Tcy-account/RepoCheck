<template>
  <el-container class="main-layout">
    <el-header class="header">
      <div class="logo" @click="$router.push('/home')">
        <el-icon :size="24"><Monitor /></el-icon>
        <span class="title">RepoCheck</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        mode="horizontal"
        :ellipsis="false"
        router
        class="nav-menu"
      >
        <el-menu-item index="/home">首页</el-menu-item>
        <el-menu-item index="/tasks">任务列表</el-menu-item>
        <el-menu-item index="/profile">个人中心</el-menu-item>
      </el-menu>
      <div class="header-right">
        <span v-if="userStore.user" class="user-info">
          <el-icon><UserFilled /></el-icon>
          {{ userStore.user.username }}
        </span>
        <span v-else class="subtitle">论文代码可用性检测器</span>
      </div>
    </el-header>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { UserFilled } from '@element-plus/icons-vue'

const route = useRoute()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)

onMounted(() => {
  if (localStorage.getItem('token')) {
    userStore.fetchUser()
  }
})
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 24px;
  height: 60px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin-right: 40px;
}

.logo .title {
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
}

.nav-menu {
  flex: 1;
  border-bottom: none !important;
}

.header-right {
  margin-left: auto;
}

.subtitle {
  color: #909399;
  font-size: 13px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #303133;
  font-size: 14px;
}

.main-content {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>
