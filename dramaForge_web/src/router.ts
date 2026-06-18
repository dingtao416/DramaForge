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
      meta: { auth: true },
    },
    {
      path: '/projects',
      name: 'Projects',
      component: () => import('@/views/ProjectListPage.vue'),
      meta: { auth: true },
    },
    {
      path: '/projects/:id',
      component: () => import('@/views/ProjectLayout.vue'),
      meta: { auth: true },
      children: [
        {
          path: '',
          redirect: (to) => ({ path: `/projects/${to.params.id}/script` }),
        },
        {
          path: 'script',
          name: 'Script',
          component: () => import('@/views/ScriptPage.vue'),
          meta: { auth: true },
        },
        {
          path: 'assets',
          name: 'Assets',
          component: () => import('@/views/AssetsPage.vue'),
          meta: { auth: true },
        },
        {
          path: 'episodes',
          name: 'Episodes',
          component: () => import('@/views/EpisodesPage.vue'),
          meta: { auth: true },
        },
      ],
    },
    {
      path: '/projects/:id/episodes/:epId/storyboard',
      name: 'StoryboardEditor',
      component: () => import('@/views/StoryboardEditorPage.vue'),
      meta: { auth: true },
    },
    {
      path: '/drama-workbench',
      name: 'DramaWorkbench',
      component: () => import('@/views/DramaWorkbenchPage.vue'),
      meta: { auth: true },
    },
    {
      path: '/assets',
      name: 'AssetLibrary',
      component: () => import('@/views/AssetLibraryPage.vue'),
      meta: { auth: true },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/SettingsPage.vue'),
      meta: { auth: true },
    },
    // Catch-all: redirect unknown routes to home
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// ── Navigation guard ──
router.beforeEach((to, _from, next) => {
  // Redirect authenticated users away from guest-only pages (login)
  if (to.meta.guest && isAuthenticated()) {
    return next('/')
  }
  // Redirect unauthenticated users to login for protected pages
  if (to.meta.auth && !isAuthenticated()) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }
  next()
})

export default router
