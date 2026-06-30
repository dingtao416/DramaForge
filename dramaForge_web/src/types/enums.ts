export const ProjectStep = {
  SCRIPT: 'script',
  ASSETS: 'assets',
  STORYBOARD: 'storyboard',
  COMPLETED: 'completed',
} as const
export type ProjectStep = typeof ProjectStep[keyof typeof ProjectStep]

export const VideoStyle = {
  REALISTIC: 'realistic',
  ANIME: 'anime',
  CARTOON: 'cartoon',
  CINEMATIC: 'cinematic',
  WATERCOLOR: 'watercolor',
  INK_WASH: 'ink_wash',
} as const
export type VideoStyle = typeof VideoStyle[keyof typeof VideoStyle]

export const DramaGenre = {
  ROMANCE: 'romance',
  SUSPENSE: 'suspense',
  COMEDY: 'comedy',
  FANTASY: 'fantasy',
  URBAN: 'urban',
  HISTORICAL: 'historical',
  REVENGE: 'revenge',
  THRILLER: 'thriller',
  OTHER: 'other',
} as const
export type DramaGenre = typeof DramaGenre[keyof typeof DramaGenre]

export const CharacterRole = {
  PROTAGONIST: 'protagonist',
  ANTAGONIST: 'antagonist',
  SUPPORTING: 'supporting',
  EXTRA: 'extra',
  NARRATOR: 'narrator',
} as const
export type CharacterRole = typeof CharacterRole[keyof typeof CharacterRole]

export const SegmentStatus = {
  PENDING: 'pending',
  GENERATING: 'generating',
  COMPLETED: 'completed',
  PARTIAL: 'partial',
  FAILED: 'failed',
} as const
export type SegmentStatus = typeof SegmentStatus[keyof typeof SegmentStatus]

export const CameraType = {
  CLOSE_UP: 'close_up',
  MEDIUM: 'medium',
  FULL: 'full',
  WIDE: 'wide',
  EXTREME_CLOSE: 'extreme_close',
  OVER_SHOULDER: 'over_shoulder',
  POV: 'pov',
  AERIAL: 'aerial',
} as const
export type CameraType = typeof CameraType[keyof typeof CameraType]

export const CameraMovement = {
  STATIC: 'static',
  PAN: 'pan',
  TILT: 'tilt',
  ZOOM_IN: 'zoom_in',
  ZOOM_OUT: 'zoom_out',
  DOLLY: 'dolly',
  TRACKING: 'tracking',
  HANDHELD: 'handheld',
} as const
export type CameraMovement = typeof CameraMovement[keyof typeof CameraMovement]

export const VideoStyleLabel: Record<VideoStyle, string> = {
  [VideoStyle.REALISTIC]: '真人写实',
  [VideoStyle.ANIME]: '动漫风格',
  [VideoStyle.CARTOON]: '卡通风格',
  [VideoStyle.CINEMATIC]: '电影质感',
  [VideoStyle.WATERCOLOR]: '水彩风格',
  [VideoStyle.INK_WASH]: '水墨风格',
}

export const DramaGenreLabel: Record<DramaGenre, string> = {
  [DramaGenre.ROMANCE]: '甜宠',
  [DramaGenre.SUSPENSE]: '悬疑',
  [DramaGenre.COMEDY]: '搞笑',
  [DramaGenre.FANTASY]: '奇幻',
  [DramaGenre.URBAN]: '都市',
  [DramaGenre.HISTORICAL]: '古装',
  [DramaGenre.REVENGE]: '复仇',
  [DramaGenre.THRILLER]: '惊悚',
  [DramaGenre.OTHER]: '其他',
}

export const ProjectStepLabel: Record<ProjectStep, string> = {
  [ProjectStep.SCRIPT]: 'Story Bible & 剧本',
  [ProjectStep.ASSETS]: '角色与场景资产',
  [ProjectStep.STORYBOARD]: '分镜与成片',
  [ProjectStep.COMPLETED]: '已完成',
}

export const CharacterRoleLabel: Record<CharacterRole, string> = {
  [CharacterRole.PROTAGONIST]: '主角',
  [CharacterRole.ANTAGONIST]: '反派',
  [CharacterRole.SUPPORTING]: '配角',
  [CharacterRole.EXTRA]: '群演',
  [CharacterRole.NARRATOR]: '旁白',
}

export const SegmentStatusLabel: Record<SegmentStatus, string> = {
  [SegmentStatus.PENDING]: '待生成',
  [SegmentStatus.GENERATING]: '生成中',
  [SegmentStatus.COMPLETED]: '已完成',
  [SegmentStatus.PARTIAL]: '部分完成',
  [SegmentStatus.FAILED]: '失败',
}

export const CameraTypeLabel: Record<CameraType, string> = {
  [CameraType.CLOSE_UP]: '特写',
  [CameraType.MEDIUM]: '中景',
  [CameraType.FULL]: '全景',
  [CameraType.WIDE]: '远景',
  [CameraType.EXTREME_CLOSE]: '大特写',
  [CameraType.OVER_SHOULDER]: '过肩',
  [CameraType.POV]: '主观视角',
  [CameraType.AERIAL]: '航拍',
}

export const CameraMovementLabel: Record<CameraMovement, string> = {
  [CameraMovement.STATIC]: '固定',
  [CameraMovement.PAN]: '摇',
  [CameraMovement.TILT]: '俯仰',
  [CameraMovement.ZOOM_IN]: '推',
  [CameraMovement.ZOOM_OUT]: '拉',
  [CameraMovement.DOLLY]: '移',
  [CameraMovement.TRACKING]: '跟',
  [CameraMovement.HANDHELD]: '手持',
}
