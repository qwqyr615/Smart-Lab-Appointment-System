<template>
  <div style="width: 40%">
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">修改密码</div>
      </template>
      <el-form
        ref="ruleFormRef"
        :rules="rules"
        :model="form"
        label-width="80px"
        style="width: 100%; padding-right: 50px"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input
            v-model="form.oldPassword"
            type="password"
            show-password
            placeholder="请输入原密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="form.newPassword"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="conFirmPassword">
          <el-input
            v-model="form.conFirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">确认修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
<script setup>
import { updatePassword } from '@/api/user'
import router from '@/router'
import { logout } from '@/utils/auth'
import { ElMessage } from 'element-plus'
import { ref, reactive } from 'vue'

const submitting = ref(false)
const ruleFormRef = ref()

const form = reactive({
  oldPassword: '',
  newPassword: '',
  conFirmPassword: ''
})

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入新密码'))
  } else if (value !== form.newPassword) {
    callback(new Error('两次密码输入不一致'))
  } else {
    callback()
  }
}

const rules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
  conFirmPassword: [{ validator: validatePass, trigger: 'blur' }]
}

const handleSubmit = async () => {
  const valid = await ruleFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const res = await updatePassword({
      old_password: form.oldPassword,
      new_password: form.newPassword
    })
    if (res.code === 200) {
      ElMessage.success('密码修改成功，请重新登录')
      logout()
      await router.push('/login')
    }
  } finally {
    submitting.value = false
  }
}
</script>
<style scope></style>
