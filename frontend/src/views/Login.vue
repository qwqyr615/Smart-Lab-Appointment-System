<template>
  <div class="login-container">
    <div class="login-box">
      <h1 style="font-size: 24px">实验室预约系统</h1>
      <div style="margin-top: 5px; margin-bottom: 30px">基于Agent智能预约系统</div>
      <el-form
        ref="ruleFormRef"
        :rules="rules"
        :model="form"
        label-width="auto"
        style="max-width: 600px"
      >
        <el-form-item prop="username">
          <el-input
            size="large"
            v-model="form.username"
            placeholder="请输入账号"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            type="password"
            size="large"
            v-model="form.password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <div>
          <el-button
            size="large"
            type="primary"
            style="width: 100%"
            @click="login"
            :loading="loadingValue"
            >登 录</el-button
          >
          <div style="text-align: right; margin-top: 20px">
            还没有账号？请
            <router-link style="color: var(--el-color-primary)" to="/register">注册</router-link>
          </div>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { loginAPi } from '@/api/auth'
import { useUser } from '@/utils/user'
const { saveLoginData } = useUser()

const ruleFormRef = ref()

const form = reactive({
  username: '',
  password: ''
})

const loadingValue = ref(false)

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const login = async () => {
  const valid = await ruleFormRef.value.validate().catch(() => false)
  if (!valid) return
  loadingValue.value = true
  try {
    const response = await loginAPi(form)
    if (response.code === 200) {
      saveLoginData(response.data)
      ElMessage.success('登录成功')
      await router.push('/manager/home')
      console.log('跳转结束')
    }
  } finally {
    loadingValue.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}
.login-box {
  width: 380px;
  border-radius: 8px;
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1);
  padding: 30px;
  text-align: center;
  background-color: white;
}
</style>
