/* ─── DramaForge v2.0 — Enum Types (对齐后端 Python 枚举) ─── */

export enum ProjectStep {
  SCRIPT = 'script',
  ASSETS = 'assets',
  STORYBOARD = 'storyboard',
  COMPLETED = 'completed',
}

export enum VideoStyle {
  REALISTIC = 'realistic',
  ANIME = 'anime',
  THREE_D = '3d',
  CLAY = 'clay',
  WATERCOLOR = 'watercolor',
}

export enum DramaGenre {
  FEMALE = 'female',
  MALE = 'male',
  URBAN = 'urban',
  ANCIENT = 'ancient',
  SUSPENSE = 'suspense',
  COMEDY = 'comedy',
  SCI_FI = 'sci_fi',
  OTHER = 'other',
}

export enum CharacterRole {
  PROTAGONIST = 'protagonist',
  SUPPORTING = 'supporting',
  EXTRA = 'extra',
  NARRATOR = 'narrator',
}

export enum SegmentStatus {
  PENDING = 'pending',
  GENERATING = 'generating',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum CameraType {
  CLOSE_UP = 'close_up',
  MEDIUM = 'medium',
  WIDE = 'wide',
  EXTREME_CLOSE_UP = 'extreme_close_up',
  EXTREME_WIDE = 'extreme_wide',
  OVER_SHOULDER = 'over_shoulder',
}

export enum CameraMovement {
  STATIC = 'static',
  PAN_LEFT = 'pan_left',
  PAN_RIGHT = 'pan_right',
  TILT_UP = 'tilt_up',
  TILT_DOWN = 'tilt_down',
  ZOOM_IN = 'zoom_in',
  ZOOM_OUT = 'zoom_out',
  TRACKING = 'tracking',
  DOLLY = 'dolly',
}

/* Display label maps */

export const VideoStyleLabel: Record<VideoStyle, string> = {
  [VideoStyle.REALISTIC]: '真人写实',
  [VideoStyle.ANIME]: '动漫风格',
  [VideoStyle.THREE_D]: '3D 动画',
  [VideoStyle.CLAY]: '黏土动画',
  [VideoStyle.WATERCOLOR]: '水彩风格',
}

export const DramaGenreLabel: Record<DramaGenre, string> = {
  [DramaGenre.FEMALE]: '女频',
  [DramaGenre.MALE]: '男频',
  [DramaGenre.URBAN]: '都市',
  [DramaGenre.ANCIENT]: '古装',
  [DramaGenre.SUSPENSE]: '悬疑',
  [DramaGenre.COMEDY]: '喜剧',
  [DramaGenre.SCI_FI]: '科幻',
  [DramaGenre.OTHER]: '其他',
}

export const ProjectStepLabel: Record<ProjectStep, string> = {
  [ProjectStep.SCRIPT]: '剧本大纲',
  [ProjectStep.ASSETS]: '角色和场景',
  [ProjectStep.STORYBOARD]: '分集视频',
  [ProjectStep.COMPLETED]: '已完成',
}

export const CharacterRoleLabel: Record<CharacterRole, string> = {
  [CharacterRole.PROTAGONIST]: '主角',
  [CharacterRole.SUPPORTING]: '配角',
  [CharacterRole.EXTRA]: '龙套',
  [CharacterRole.NARRATOR]: '旁白',
}

export const SegmentStatusLabel: Record<SegmentStatus, string> = {
  [SegmentStatus.PENDING]: '待生成',
  [SegmentStatus.GENERATING]: '生成中',
  [SegmentStatus.COMPLETED]: '已完成',
  [SegmentStatus.FAILED]: '失败',
}