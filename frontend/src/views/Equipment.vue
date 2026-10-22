<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">实验室设备管理</div>
      </template>
      <div style="margin-bottom: 10px">
        <el-input
          placeholder="请输入名称查询"
          v-model="params.keywords"
          style="width: 240px; margin-right: 8px"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        ></el-input>
        <el-select
          v-model="params.lab_id"
          placeholder="请选择实验室"
          style="width: 200px; margin-right: 8px"
          clearable
        >
          <el-option v-for="item in options" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button type="success" :icon="Plus" @click="handleCreate">新增</el-button>
      </div>
      <el-table
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#333' }"
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="lab_name" label="所属实验室" width="150" />
        <el-table-column prop="name" label="设备名称" />
        <el-table-column prop="img" label="图片" width="90">
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
        <el-table-column prop="spec" label="型号规格" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '正常' : '维修' }}
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
        label-width="100px"
        style="width: 100%; padding-right: 30px; padding-top: 16px"
      >
        <el-form-item label="所属实验室" prop="lab_id">
          <el-select v-model="form.lab_id" placeholder="请选择实验室" style="width: 100%">
            <el-option v-for="item in options" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入说明" />
        </el-form-item>
        <el-form-item label="图片">
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
        <el-form-item label="型号规格">
          <el-input v-model="form.spec" placeholder="例如 RTX4090 24G" />
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="form.quantity" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">维修</el-radio>
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
import {
  createEquipment,
  getEquipmentPageList,
  updateEquipment,
  deleteEquipment
} from '@/api/equipment'
import { uploadFile } from '@/api/file'
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getLabPageList } from '@/api/lab'

const params = reactive({
  page: 1,
  pageSize: 10,
  keywords: '',
  lab_id: null
})

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const ruleFormRef = ref()
const formLoading = ref(false)
const options = ref([])

const form = reactive({
  id: null,
  lab_id: null,
  name: '',
  description: '',
  img: '',
  spec: '',
  quantity: 1,
  status: 1
})

const rules = {
  lab_id: [{ required: true, message: '请选择实验室', trigger: 'change' }],
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }]
}

const handleFileUpload = async ({ file }) => {
  const res = await uploadFile(file)
  form.img = res.data?.url ?? ''
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
    lab_id: null,
    name: '',
    description: '',
    img: '',
    spec: '',
    quantity: 1,
    status: 1
  })
}

const handleCreate = () => {
  resetForm()
  dialogVisible.value = true
  nextTick(() => ruleFormRef.value?.clearValidate())
}

const handleEdit = (row) => {
  resetForm()
  Object.assign(form, {
    id: row.id,
    lab_id: row.lab_id,
    name: row.name,
    description: row.description ?? '',
    img: row.img ?? '',
    spec: row.spec ?? '',
    quantity: row.quantity,
    status: row.status
  })
  dialogVisible.value = true
  nextTick(() => ruleFormRef.value?.clearValidate())
}

// 删除设备
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除设备 ${row.name} ？`, '确认删除', {
      type: 'warning'
    })
  } catch {
    return
  }

  const res = await deleteEquipment(row.id)
  if (res.code === 200) {
    ElMessage.success('删除设备成功')
    const lastPage = Math.max(1, Math.ceil((total.value - 1) / params.pageSize))
    params.page = Math.min(params.page, lastPage)
    await load()
  }
}

// 保存设备
const handleSave = async () => {
  const valid = await ruleFormRef.value.validate().catch(() => false)
  if (!valid) return
  formLoading.value = true
  try {
    const { id, ...data } = form
    const res = id ? await updateEquipment(id, data) : await createEquipment(data)
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
    const res = await getEquipmentPageList({
      page: params.page,
      page_size: params.pageSize,
      keywords: params.keywords,
      ...(params.lab_id != null ? { lab_id: params.lab_id } : {})
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

const loadLabs = async () => {
  const pageSize = 100
  const labs = []
  let page = 1

  while (true) {
    const res = await getLabPageList({ page, page_size: pageSize })
    const items = res.data?.list ?? []
    labs.push(...items)
    if (items.length < pageSize || labs.length >= (res.data?.total ?? Infinity)) break
    page += 1
  }

  options.value = labs
}

onMounted(() => {
  loadLabs()
  load()
})
</script>

<style scoped>
.avatar-uploader .avatar {
  width: 130px;
  height: 130px;
  display: block;
  object-fit: cover;
}
.avatar-uploader :deep(.el-upload) {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}
.avatar-uploader :deep(.el-upload:hover) {
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
