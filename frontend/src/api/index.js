/**
 * 接口封装：与接口文档第 7 章一一对应。
 * 所有函数返回 data 字段内容，失败抛 ApiError。
 */

import http from './client'

/* ---------------------------------------------------------------- 认证 */
export const authApi = {
  register: (data) => http.post('/auth/register', data, { auth: false }),
  login: (data) => http.post('/auth/login', data, { auth: false }),
  logout: (token) => http.post('/auth/logout', { token }, { auth: false }),
}

/* ---------------------------------------------------------------- 用户 */
export const userApi = {
  me: () => http.get('/users/me'),
  updateMe: (data) => http.put('/users/me', data),
  changePassword: (data) => http.put('/users/me/password', data),
  // 管理端
  list: (params) => http.get('/admin/users', params),
  updateStatus: (userId, status) => http.put(`/admin/users/${userId}/status`, { status }),
  updateRoles: (userId, roleCodes) =>
    http.put(`/admin/users/${userId}/roles`, { role_codes: roleCodes }),
}

/* ---------------------------------------------------------------- 角色 */
export const roleApi = {
  list: () => http.get('/admin/roles'),
  create: (data) => http.post('/admin/roles', data),
  update: (roleId, data) => http.put(`/admin/roles/${roleId}`, data),
  remove: (roleId) => http.del(`/admin/roles/${roleId}`),
}

/* ---------------------------------------------------------------- 活动 */
export const activityApi = {
  // 公开
  listPublic: () => http.get('/activities', null, { auth: false }),
  getPublic: (id) => http.get(`/activities/${id}`, null, { auth: false }),
  // 管理端
  list: (params) => http.get('/admin/activities', params),
  create: (data) => http.post('/admin/activities', data),
  get: (id) => http.get(`/admin/activities/${id}`),
  update: (id, data) => http.put(`/admin/activities/${id}`, data),
  remove: (id) => http.del(`/admin/activities/${id}`),
  transition: (id, action) => http.post(`/admin/activities/${id}/${action}`),
}

/* ---------------------------------------------------------------- 奖品 */
export const prizeApi = {
  // 公开
  listByActivity: (activityId) => http.get(`/activities/${activityId}/prizes`, null, { auth: false }),
  // 管理端
  list: (params) => http.get('/admin/prizes', params),
  create: (data) => http.post('/admin/prizes', data),
  get: (id) => http.get(`/admin/prizes/${id}`),
  update: (id, data) => http.put(`/admin/prizes/${id}`, data),
  adjustStock: (id, data) => http.put(`/admin/prizes/${id}/stock`, data),
  remove: (id) => http.del(`/admin/prizes/${id}`),
}

export const categoryApi = {
  list: () => http.get('/admin/prize-categories'),
  create: (data) => http.post('/admin/prize-categories', data),
  update: (id, data) => http.put(`/admin/prize-categories/${id}`, data),
  remove: (id) => http.del(`/admin/prize-categories/${id}`),
}

/* ---------------------------------------------------------------- 文件 */
export const fileApi = {
  uploadUserImage: (formData) => http.upload('/files/images', formData),
  uploadAdminImage: (formData) => http.upload('/admin/files/images', formData),
}

/* ---------------------------------------------------------------- 抽奖 */
export const lotteryApi = {
  draw: (activityId) => http.post(`/lottery/${activityId}/draw`),
  myRecords: (params) => http.get('/lottery/records', params),
  recordByOrderNo: (orderNo) => http.get(`/lottery/records/${encodeURIComponent(orderNo)}`),
}

/* ---------------------------------------------------------------- 中奖 */
export const winningApi = {
  mine: (params) => http.get('/winnings/me', params),
  myDetail: (winId) => http.get(`/winnings/me/${winId}`),
  claim: (winId, data) => http.post(`/winnings/${winId}/claim`, data),
  // 运营端
  list: (params) => http.get('/admin/winnings', params),
  updateStatus: (winId, data) => http.patch(`/admin/winnings/${winId}/status`, data),
}

/* ---------------------------------------------------------------- 补发 */
export const rewardApi = {
  list: (params) => http.get('/admin/rewards', params),
  create: (data) => http.post('/admin/rewards/manual', data),
  updateStatus: (rewardId, data) => http.patch(`/admin/rewards/${rewardId}/status`, data),
}

/* ---------------------------------------------------------------- 运营查询 */
export const operationsApi = {
  users: (params) => http.get('/operations/users', params),
  prizes: (params) => http.get('/operations/prizes', params),
}

/* ---------------------------------------------------------------- 统计 */
export const statisticsApi = {
  activity: (activityId) => http.get(`/admin/statustics/activities/${activityId}`),
}

export default {
  authApi,
  userApi,
  roleApi,
  activityApi,
  prizeApi,
  categoryApi,
  fileApi,
  lotteryApi,
  winningApi,
  rewardApi,
  operationsApi,
  statisticsApi,
}
