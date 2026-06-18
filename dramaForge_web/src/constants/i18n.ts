/**
 * DramaForge i18n — UI String Constants
 * ======================================
 * Centralized UI strings for future i18n support.
 * Currently primary: zh-CN, secondary: en.
 *
 * Usage: import { t } from '@/constants/i18n'
 *         t('common.save')  →  '保存'
 *
 * To switch language, change `currentLocale` at runtime.
 */

export type Locale = 'zh-CN' | 'en'

let currentLocale: Locale = 'zh-CN'

export function setLocale(locale: Locale) {
  currentLocale = locale
}

export function getLocale(): Locale {
  return currentLocale
}

/** Simple translation function */
export function t(key: string): string {
  const keys = key.split('.')
  let node: any = messages[currentLocale]
  for (const k of keys) {
    if (node && typeof node === 'object' && k in node) {
      node = node[k]
    } else {
      // Fallback to zh-CN
      let fallback: any = messages['zh-CN']
      for (const fk of keys) {
        if (fallback && typeof fallback === 'object' && fk in fallback) {
          fallback = fallback[fk]
        } else {
          return key // Return raw key if not found
        }
      }
      return typeof fallback === 'string' ? fallback : key
    }
  }
  return typeof node === 'string' ? node : key
}

// ═══════════════════════════════════════════════════════════════════
// Message catalog
// ═══════════════════════════════════════════════════════════════════

const messages: Record<Locale, Record<string, any>> = {
  'zh-CN': {
    common: {
      save: '保存',
      cancel: '取消',
      delete: '删除',
      edit: '编辑',
      create: '创建',
      confirm: '确认',
      back: '返回',
      next: '下一步',
      previous: '上一步',
      download: '下载',
      export: '导出',
      import: '导入',
      upload: '上传',
      regenerate: '重新生成',
      loading: '加载中...',
      noData: '暂无数据',
      success: '操作成功',
      error: '操作失败',
      retry: '重试',
      close: '关闭',
      search: '搜索',
      filter: '筛选',
      all: '全部',
      selected: '已选择',
      actions: '操作',
      settings: '设置',
      preview: '预览',
    },
    project: {
      title: '项目',
      create: '创建项目',
      duplicate: '复制项目',
      delete: '删除项目',
      list: '项目列表',
      empty: '还没有项目',
      emptyHint: '从首页开始创作你的第一个短剧项目',
      status: {
        script: '剧本阶段',
        assets: '资产阶段',
        storyboard: '分镜阶段',
        completed: '已完成',
      },
    },
    script: {
      title: '剧本',
      generate: 'AI 生成剧本',
      upload: '上传剧本文件',
      edit: '编辑剧本',
      approve: '审核通过',
      export: '导出剧本',
      rewrite: '改写为旁白型',
      protagonist: '主角',
      genre: '故事类型',
      synopsis: '故事梗概',
      background: '故事背景',
      setting: '故事设定',
      oneLiner: '一句话故事',
      episodes: '剧集内容',
      episode: '集',
      noContent: '暂无内容',
      missing: '暂无剧本',
      missingHint: '请从首页开始创作或上传剧本',
    },
    assets: {
      title: '角色与场景',
      character: '角色',
      scene: '场景',
      generate: '生成全部素材',
      regenerate: '重新生成',
      regenerateImage: '重新生成图片',
      library: '资产库',
      variants: '变体',
      variantCount: '生成变体数',
      noCharacter: '暂无角色',
      noScene: '暂无场景',
    },
    storyboard: {
      title: '分镜编辑器',
      generate: '生成分镜脚本',
      generateAssets: '生成素材',
      regenerateAssets: '重新生成',
      compose: '合成全集',
      composing: '合成中...',
      addShot: '添加分镜',
      deleteShot: '删除分镜',
      editScript: '编辑脚本',
      undo: '撤销',
      redo: '重做',
      batchUpdate: '批量更新',
      generateAll: '全部生成',
      pending: '待生成',
      generating: '生成中',
      completed: '已完成',
      failed: '生成失败',
      noStoryboard: '尚未生成分镜脚本',
      noStoryboardHint: 'AI 将根据剧本和角色场景设定自动拆分镜头',
      composeOptions: '合成选项',
      quality: '视频质量',
      qualityHigh: '高',
      qualityMedium: '中',
      qualityLow: '低',
      resolution: '分辨率',
      bgm: '背景音乐',
      bgmUpload: '选择文件',
      bgmUploaded: '已上传',
      bgmVolume: '音量',
      subtitle: '片头字幕',
      subtitlePlaceholder: '输入字幕文本（留空不添加）',
      subtitleFontSize: '字号',
    },
    chat: {
      title: '对话',
      send: '发送',
      placeholder: '描述你的想法...',
      newConversation: '新建对话',
      history: '历史记录',
      modes: {
        general: '通用模式',
        scriptwriter: '编剧模式',
        director: '导演模式',
        project: '项目模式',
      },
    },
    billing: {
      title: '计费',
      balance: '积分余额',
      subscribe: '订阅',
      plans: '套餐方案',
      transactions: '交易记录',
    },
    payment: {
      title: '支付',
      wechat: '微信支付',
      alipay: '支付宝',
      douyin: '抖音支付',
      qrCode: '扫码支付',
      orderNo: '订单号',
      amount: '金额',
      status: '支付状态',
      paid: '已支付',
      pending: '待支付',
    },
    user: {
      login: '登录',
      register: '注册',
      logout: '退出登录',
      profile: '个人中心',
      settings: '账号设置',
      aiConfig: 'AI 配置',
      apiKey: 'API 密钥',
      modelConfig: '模型配置',
    },
    notification: {
      scriptGenerated: '剧本生成完成',
      assetsGenerated: '素材生成完成',
      videoComposed: '视频合成完成',
      segmentGenerating: '片段素材生成中...',
      segmentFailed: '片段生成失败',
    },
  },

  'en': {
    common: {
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      edit: 'Edit',
      create: 'Create',
      confirm: 'Confirm',
      back: 'Back',
      next: 'Next',
      previous: 'Previous',
      download: 'Download',
      export: 'Export',
      import: 'Import',
      upload: 'Upload',
      regenerate: 'Regenerate',
      loading: 'Loading...',
      noData: 'No data',
      success: 'Success',
      error: 'Error',
      retry: 'Retry',
      close: 'Close',
      search: 'Search',
      filter: 'Filter',
      all: 'All',
      selected: 'Selected',
      actions: 'Actions',
      settings: 'Settings',
      preview: 'Preview',
    },
    project: {
      title: 'Projects',
      create: 'Create Project',
      duplicate: 'Duplicate Project',
      delete: 'Delete Project',
      list: 'Project List',
      empty: 'No projects yet',
      emptyHint: 'Start creating your first short drama project',
      status: {
        script: 'Script Stage',
        assets: 'Assets Stage',
        storyboard: 'Storyboard Stage',
        completed: 'Completed',
      },
    },
    script: {
      title: 'Script',
      generate: 'AI Generate Script',
      upload: 'Upload Script File',
      edit: 'Edit Script',
      approve: 'Approve',
      export: 'Export Script',
      rewrite: 'Rewrite as Narration',
      protagonist: 'Protagonist',
      genre: 'Genre',
      synopsis: 'Synopsis',
      background: 'Background',
      setting: 'Setting',
      oneLiner: 'One-liner',
      episodes: 'Episodes',
      episode: 'Episode',
      noContent: 'No content',
      missing: 'No script yet',
      missingHint: 'Start creating or uploading a script from the homepage',
    },
    assets: {
      title: 'Characters & Scenes',
      character: 'Character',
      scene: 'Scene',
      generate: 'Generate All Assets',
      regenerate: 'Regenerate',
      regenerateImage: 'Regenerate Image',
      library: 'Asset Library',
      variants: 'Variants',
      variantCount: 'Variant Count',
      noCharacter: 'No characters',
      noScene: 'No scenes',
    },
    storyboard: {
      title: 'Storyboard Editor',
      generate: 'Generate Storyboard',
      generateAssets: 'Generate Assets',
      regenerateAssets: 'Regenerate',
      compose: 'Compose Episode',
      composing: 'Composing...',
      addShot: 'Add Shot',
      deleteShot: 'Delete Shot',
      editScript: 'Edit Script',
      undo: 'Undo',
      redo: 'Redo',
      batchUpdate: 'Batch Update',
      generateAll: 'Generate All',
      pending: 'Pending',
      generating: 'Generating',
      completed: 'Completed',
      failed: 'Failed',
      noStoryboard: 'No storyboard generated yet',
      noStoryboardHint: 'AI will split shots based on the script and character/scene settings',
      composeOptions: 'Compose Options',
      quality: 'Video Quality',
      qualityHigh: 'High',
      qualityMedium: 'Medium',
      qualityLow: 'Low',
      resolution: 'Resolution',
      bgm: 'Background Music',
      bgmUpload: 'Select File',
      bgmUploaded: 'Uploaded',
      bgmVolume: 'Volume',
      subtitle: 'Opening Subtitle',
      subtitlePlaceholder: 'Enter subtitle text (leave empty to skip)',
      subtitleFontSize: 'Font Size',
    },
    chat: {
      title: 'Chat',
      send: 'Send',
      placeholder: 'Describe your idea...',
      newConversation: 'New Conversation',
      history: 'History',
      modes: {
        general: 'General',
        scriptwriter: 'Scriptwriter',
        director: 'Director',
        project: 'Project',
      },
    },
    billing: {
      title: 'Billing',
      balance: 'Credit Balance',
      subscribe: 'Subscribe',
      plans: 'Plans',
      transactions: 'Transactions',
    },
    payment: {
      title: 'Payment',
      wechat: 'WeChat Pay',
      alipay: 'Alipay',
      douyin: 'Douyin Pay',
      qrCode: 'Scan QR Code',
      orderNo: 'Order No.',
      amount: 'Amount',
      status: 'Payment Status',
      paid: 'Paid',
      pending: 'Pending',
    },
    user: {
      login: 'Login',
      register: 'Register',
      logout: 'Logout',
      profile: 'Profile',
      settings: 'Settings',
      aiConfig: 'AI Config',
      apiKey: 'API Key',
      modelConfig: 'Model Config',
    },
    notification: {
      scriptGenerated: 'Script generation complete',
      assetsGenerated: 'Asset generation complete',
      videoComposed: 'Video composition complete',
      segmentGenerating: 'Generating segment assets...',
      segmentFailed: 'Segment generation failed',
    },
  },
}
