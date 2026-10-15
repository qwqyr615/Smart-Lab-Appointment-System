// 仅供页面  setup 函数使用
// Hook
import { ref } from 'vue'
import { getUserInfo, setToken, setUserInfo } from './auth'

const userInfo = ref(getUserInfo()) //响应式对象 可以随时更新最新的值

export function useUser() {
  // 登录成功后，保存token和用户信息
  function saveLoginData(data) {
    setToken(data.token)
    setUserInfo(data.user)
    // 将内存中的user更新
    userInfo.value = data.user
  }

  // 用户信息修改后，更新本地存储和页面
  function updateUser(user) {
    setUserInfo(user)
    userInfo.value = user
  }

  // 从 localStorage 重新读取最新数据
  function reloadUser(user) {
    userInfo.value = getUserInfo()
  }

  // Hook的出口
  return {
    userInfo,
    saveLoginData,
    updateUser,
    reloadUser
  }
}
