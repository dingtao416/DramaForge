import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '@/api/client'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginPage.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/HomePage.vue'),
    },
    {
      path: '/projects',
      name: 'Projects',
      component: () => import('@/views/ProjectListPage.vue'),
    },
    {
      path: '/projects/:id',
      component: () => import('@/views/ProjectLayout.vue'),
      children: [
        {
          path: '',
          redirect: (to) => ({ path: `/projects/${to.params.id}/script` }),
        },
        {
          path: 'script',
          name: 'Script',
          component: () => import('@/views/ScriptPage.vue'),
        },
        {
          path: 'assets',
          name: 'Assets',
          component: () => import('@/views/AssetsPage.vue'),
        },
        {
          path: 'episodes',
          name: 'Episodes',
          component: () => import('@/views/EpisodesPage.vue'),
        },
        {
          path: 'episodes/:epId/storyboard',
          name: 'StoryboardEditor',
          component: () => import('@/views/StoryboardEditorPage.vue'),
        },
      ],
    },
    {
      path: '/drama-workbench',
      name: 'DramaWorkbench',
      component: () => import('@/views/DramaWorkbenchPage.vue'),
    },
    {
      path: '/assets',
      name: 'AssetLibrary',
      component: () => import('@/views/AssetLibraryPage.vue'),
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/SettingsPage.vue'),
    },
  ],
})

// ── Navigation guard ──
// TODO: 上线前取消注释，启用强制登录
router.beforeEach((to, _from, next) => {
  // Guest routes (login/register) — redirect to home if already logged in
  if (to.meta.guest && isAuthenticated()) {
    return next('/')
  }
  // 开发阶段：不强制跳转登录，允许自由浏览
  // if (!to.meta.guest && to.name !== 'Login' && !isAuthenticated()) {
  //   return next('/login')
  // }
  next()
})

export default router