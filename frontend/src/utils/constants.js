/**
 * 后端枚举与展示映射。
 * 取值与 app/models/enums.py 保持一致。
 */

export const ACTIVITY_STATUS = {
  draft: { label: '草稿', cls: 'st-draft', desc: '尚未发布，仅管理端可见' },
  pending: { label: '待开始', cls: 'st-pending', desc: '已发布，等待开始时间' },
  ongoing: { label: '进行中', cls: 'st-ongoing', desc: '可以抽奖' },
  paused: { label: '已暂停', cls: 'st-paused', desc: '暂停期间不可抽奖' },
  ended: { label: '已结束', cls: 'st-ended', desc: '活动已结束' },
}

export const PRIZE_TYPE = {
  physical: { label: '实物', cls: 'st-brand' },
  virtual: { label: '虚拟', cls: 'st-info' },
}

export const PRIZE_STATUS = {
  enabled: { label: '启用', cls: 'st-success' },
  disabled: { label: '停用', cls: 'st-neutral' },
}

export const DRAW_STATUS = {
  pending: { label: '处理中', cls: 'st-pending' },
  won: { label: '已中奖', cls: 'st-won' },
  no_prize: { label: '未中奖', cls: 'st-neutral' },
  failed: { label: '处理失败', cls: 'st-danger' },
  refunded: { label: '已回补', cls: 'st-warning' },
}

export const REDEMPTION_STATUS = {
  pending: { label: '待填写', cls: 'st-pending' },
  submitted: { label: '已提交', cls: 'st-info' },
  processing: { label: '处理中', cls: 'st-brand' },
  completed: { label: '已发放', cls: 'st-success' },
  cancelled: { label: '已取消', cls: 'st-neutral' },
}

export const REWARD_STATUS = {
  pending: { label: '待发放', cls: 'st-pending' },
  issued: { label: '已发放', cls: 'st-success' },
  cancelled: { label: '已取消', cls: 'st-neutral' },
}

export const USER_STATUS = {
  active: { label: '正常', cls: 'st-success' },
  disabled: { label: '已禁用', cls: 'st-danger' },
}

export const ROLE_STATUS = {
  enabled: { label: '启用', cls: 'st-success' },
  disabled: { label: '停用', cls: 'st-neutral' },
}

/** 运营端可执行的状态流转（与后端状态机一致） */
export const REDEMPTION_TRANSITIONS = {
  pending: ['submitted', 'cancelled'],
  submitted: ['processing', 'cancelled'],
  processing: ['completed', 'cancelled'],
  completed: [],
  cancelled: [],
}

export const REWARD_TRANSITIONS = {
  pending: ['issued', 'cancelled'],
  issued: [],
  cancelled: [],
}

/** 活动状态机：管理端可执行的动作 */
export const ACTIVITY_ACTIONS = [
  { action: 'publish', label: '发布', from: ['draft'], to: '待开始', cls: 'btn-primary' },
  { action: 'start', label: '开始', from: ['pending'], to: '进行中', cls: 'btn-primary' },
  { action: 'pause', label: '暂停', from: ['ongoing'], to: '已暂停', cls: 'btn' },
  { action: 'resume', label: '恢复', from: ['paused'], to: '进行中', cls: 'btn-primary' },
  { action: 'end', label: '结束', from: ['pending', 'ongoing', 'paused'], to: '已结束', cls: 'btn-danger' },
]

export function meta(map, key) {
  return map[key] || { label: key || '-', cls: 'st-neutral' }
}

export const ROLE_LABEL = {
  admin: '管理员',
  operator: '运营人员',
  user: '普通用户',
}

export const PAGE_SIZE = 12
export const ADMIN_PAGE_SIZE = 15
