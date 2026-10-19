<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">实验室管理</div>
      </template>
      <div style="margin-bottom: 10px">
        <el-input
          placeholder="请输入名称或位置查询"
          v-model="params.keywords"
          style="width: 240px; margin-right: 8px"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        ></el-input>
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button type="success" :icon="Plus" @click="handleCreate">新增</el-button>
      </div>
      <el-table
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#333' }"
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="description" label="简介" />
        <el-table-column prop="img" label="封面" width="90">
          <template #default="{ row }">
            <div style="min-height: 50px">
              <img
                v-if="row.img"
                style="display: block; width: 50px; height: 50px; border-radius: 6px"
                :src="row.img"
                alt=""
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" width="100" />
        <el-table-column prop="capacity" label="容纳人数" width="100" />
        <el-table-column label="开放时间" width="140">
          <template #default="{ row }">
            {{ row.open_time && row.close_time ? `${row.open_time} - ${row.close_time}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '开放' : '关闭' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button type="primary" text bg @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" text bg @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 10px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="params.page"
          v-model:page-size="params.pageSize"
          :total="total"
          background
          layout="total, prev, pager, next"
          @current-change="load"
        />
      </div>
    </el-card>
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑' : '新增'" width="520">
      <el-form
        ref="ruleFormRef"
        :rules="rules"
        :model="form"
        label-width="90px"
        style="width: 100%; padding-right: 30px; padding-top: 16px"
      >
        <el-form-item label="封面">
          <el-upload
            class="avatar-uploader"
            :http-request="handleFileUpload"
            :show-file-list="false"
            accept="image/jpeg,image/png,image/gif,image/webp"
            :before-upload="beforeAvatarUpload"
          >
            <img v-if="form.img" :src="form.img" class="avatar" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入实验室名称" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="form.location" placeholder="请输入位置" />
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="form.capacity" :min="1" :max="500" />
        </el-form-item>
        <el-form-item label="开放时间">
          <el-time-picker
            v-model="form.open_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="开始"
            style="width: 140px; margin-right: 8px"
          />
          <el-time-picker
            v-model="form.close_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="结束"
            style="width: 140px"
          />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入简介" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">开放</el-radio>
            <el-radio :value="0">关闭</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Search, Plus } from '@element-plus/icons-vue'
import { createLab, getLabPageList, updateLab, deleteLab } from '@/api/lab'
import { uploadFile } from '@/api/file'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const params = reactive({
  page: 1,
  pageSize: 3,
  keywords: ''
})

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const ruleFormRef = ref()
const formLoading = ref(false)

const form = reactive({
  id: null,
  name: '',
  location: '',
  capacity: 20,
  open_time: '08:00',
  close_time: '18:00',
  description: '',
  img: '',
  status: 1
})

const rules = {
  name: [{ required: true, message: '请输入实验室名称', trigger: 'blur' }],
  location: [{ required: true, message: '请输入实验室位置', trigger: 'blur' }],
  capacity: [{ required: true, message: '请输入容纳人数', trigger: 'blur' }]
}

const handleFileUpload = async ({ file }) => {
  const res = await uploadFile(file)
  form.img = res.data?.url
  return res
}

const beforeAvatarUpload = (file) => {
  const imageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!imageTypes.includes(file.type)) {
    ElMessage.error('只能上传图片')
    return false
  }
  if (file.size / 1024 / 1024 > 2) {
    ElMessage.error('上传图片大小不能超过2M')
    return false
  }
  return true
}

const resetForm = () => {
  Object.assign(form, {
    id: null,
    name: '',
    location: '',
    capacity: 20,
    open_time: '08:00',
    close_time: '18:00',
    description: '',
    img: '',
    status: 1
  })
}

const handleCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  resetForm()
  Object.assign(form, {
    id: row.id,
    name: row.name,
    location: row.location,
    capacity: row.capacity,
    open_time: row.open_time,
    close_time: row.close_time,
    description: row.description,
    img: row.img,
    status: row.status
  })
  dialogVisible.value = true
}

// 删除实验室
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除实验室 ${row.name} ？`, '确认删除', {
      type: 'warning'
    })
  } catch {
    return
  }

  const res = await deleteLab(row.id)
  if (res.code === 200) {
    ElMessage.success('删除实验室成功')
    const lastPage = Math.max(1, Math.ceil((total.value - 1) / params.pageSize))
    params.page = Math.min(params.page, lastPage)
    await load()
  }
}

// 保存实验室
const handleSave = async () => {
  const valid = await ruleFormRef.value.validate().catch(() => false)
  if (!valid) return
  formLoading.value = true
  try {
    const res = form.id ? await updateLab(form.id, form) : await createLab(form)
    if (res.code === 200) {
      dialogVisible.value = false
      ElMessage.success('操作成功')
      await load()
    }
  } finally {
    formLoading.value = false
  }
}

//加载分页的数据
const load = async () => {
  try {
    loading.value = true
    const res = await getLabPageList({
      page: params.page,
      page_size: params.pageSize,
      keywords: params.keywords
    })
    if (res.code === 200) {
      tableData.value = res.data?.list ?? []
      total.value = res.data?.total ?? 0
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

<style scope>
.avatar-uploader .avatar {
  width: 130px;
  height: 130px;
  display: block;
  object-fit: cover;
}
.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}
.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}
.el-icon.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 130px;
  height: 130px;
  text-align: center;
}
</style>
