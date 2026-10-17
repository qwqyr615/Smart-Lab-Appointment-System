<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">
          <span>用户管理</span>
        </div>
      </template>
      <div style="margin-bottom: 10px">
        <el-input
          placeholder="请输入账号或名字查询"
          v-model="params.keywords"
          style="width: 200px; margin-right: 8px"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        ></el-input>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>
      <el-table
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#333' }"
        v-loading="loading"
        :data="tableData"
        style="width: 100%"
      >
        <el-table-column prop="username" label="账号" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="avatar" label="头像">
          <template #default="{ row }">
            <div style="min-height: 50px">
              <img
                v-if="row.avatar"
                style="display: block; width: 50px; height: 50px; border-radius: 50%"
                :src="row.avatar"
                alt=""
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            {{ row.role === 'admin' ? '管理员' : '学生' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'error'">
              {{ row.status === 1 ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 10px; display: flex; justify-content: flex-end">
        <el-pagination
          background
          layout="total,prev, pager, next"
          :total="total"
          v-model:page-size="params.pageSize"
          v-model:current-page="params.page"
          @current-change="load"
        />
      </div>
    </el-card>
  </div>
</template>
<script setup>
import { getUserPageList } from '@/api/user'
import { ref, reactive, onMounted } from 'vue'

const params = reactive({
  page: 1,
  pageSize: 1,
  keywords: ''
})

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

//加载分页的数据
const load = async () => {
  try {
    loading.value = true
    const res = await getUserPageList({
      page: params.page,
      page_size: params.pageSize,
      keywords: params.keywords
    })
    if (res.code == 200) {
      tableData.value = res.data?.list
      total.value = res.data?.total
    }
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  params.page = 1
  load()
}

onMounted(() => {
  load()
})
</script>
<style scope></style>
