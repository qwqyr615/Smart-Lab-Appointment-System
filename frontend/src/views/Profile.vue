<template>
  <div style="width: 50%">
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">
          <span>个人信息</span>
        </div>
      </template>
      <el-form
        ref="ruleFormRef"
        :rules="rules"
        :model="form"
        label-width="80px"
        style="width: 100%; padding-right: 50px"
      >
        <el-form-item label="头像">
          <el-upload
            class="avatar-uploader"
            :http-request="handleFileUpload"
            :show-file-list="false"
            accept="image/jpeg,image/png,image/gif,image/webp"
            :before-upload="beforeAvatarUpload"
          >
            <img v-if="form.avatar" :src="form.avatar" class="avatar" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
        </el-form-item>
        <el-form-item label="账号">
          <el-input disabled v-model="form.username" placeholer="请输入账号" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholer="请输入名称" />
        </el-form-item>
        <el-form-item label="角色">
          <el-input disabled :model-value="roleLabel" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholer="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholer="请输入手机号" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getUserInfo, updateUserInfo } from '@/api/user'
import { useUser } from '@/utils/user'
import { ElMessage } from 'element-plus'
import { uploadFileApi } from '@/api/file'
const ruleFormRef = ref()
const loadingValue = ref(false)
const submitting = ref(false)
const { updateUser } = useUser()

const form = reactive({
  username: '',
  name: '',
  role: '',
  email: '',
  phone: '',
  avatar: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式错误', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, trigger: 'blur' }]
}

const roleLabel = computed(() => {
  return form.role === 'admin' ? '管理员' : form.role === 'student' ? '学生' : '未知角色'
})

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

const handleFileUpload = async ({ file }) => {
  const res = await uploadFileApi(file)
  form.avatar = res.data?.url
  return res
}

const loadUserInfo = async () => {
  loadingValue.value = true
  try {
    const res = await getUserInfo()
    if (res.code == 200) {
      Object.assign(form, res.data)
    }
  } finally {
    loadingValue.value = false
  }
}

// 发送请求更新用户信息
const handleSubmit = async () => {
  const valid = await ruleFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const res = await updateUserInfo({
      name: form.name,
      email: form.email,
      phone: form.phone,
      avatar: form.avatar
    })
    if (res.code === 200) {
      updateUser(res.data)
      ElMessage.success('更新成功')
    }
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadUserInfo()
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
