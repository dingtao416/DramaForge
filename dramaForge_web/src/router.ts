import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
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

export default router