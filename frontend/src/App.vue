<template>
  <el-container style="min-height: 100vh">
    <el-aside width="220px" style="background: #304156">
      <div style="height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: bold; border-bottom: 1px solid #3a4a5e">
        IP 定位追踪
      </div>
      <el-menu :default-active="currentPath" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF">
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/employees">
          <el-icon><User /></el-icon>
          <span>员工列表</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <span>IP 历史</span>
        </el-menu-item>
        <el-menu-item index="/guide">
          <el-icon><Document /></el-icon>
          <span>使用说明</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-main style="background: #f0f2f5; padding: 20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentPath = computed(() => route.path)
</script>
