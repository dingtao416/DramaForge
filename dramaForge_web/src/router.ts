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
      ],
    },
    {
      path: '/projects/:id/episodes/:epId/storyboard',
      name: 'StoryboardEditor',
      component: () => import('@/views/StoryboardEditorPage.vue'),
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
router.beforeEach((to, _from, next) => {
  if (to.meta.guest && isAuthenticated()) {
    return next('/')
  }
  next()
})

export default router