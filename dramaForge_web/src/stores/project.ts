import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectsApi } from '@/api/projects'
import type { ProjectDetail, ProjectList } from '@/types/project'
import { ProjectStep } from '@/types/enums'

export const useProjectStore = defineStore('project', () => {
  // ── State ──
  const projects = ref<ProjectList[]>([])
  const currentProject = ref<ProjectDetail | null>(null)
  const loading = ref(false)

  // ── Getters ──
  const currentStep = computed<ProjectStep>(() => {
    return currentProject.value?.status || ProjectStep.SCRIPT
  })

  const stepIndex = computed(() => {
    const steps = [ProjectStep.SCRIPT, ProjectStep.ASSETS, ProjectStep.STORYBOARD, ProjectStep.COMPLETED]
    return steps.indexOf(currentStep.value)
  })

  // ── Actions ──
  async function fetchProjects() {
    loading.value = true
    try {
      const { data } = await projectsApi.list()
      projects.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id: number) {
    loading.value = true
    try {
      const { data } = await projectsApi.get(id)
      currentProject.value = data
    } finally {
      loading.value = false
    }
  }

  async function nextStep() {
    if (!currentProject.value) return
    const steps = [ProjectStep.SCRIPT, ProjectStep.ASSETS, ProjectStep.STORYBOARD, ProjectStep.COMPLETED]
    const idx = steps.indexOf(currentProject.value.status)
    if (idx < steps.length - 1) {
      const { data } = await projectsApi.update(currentProject.value.id, {
        status: steps[idx + 1],
      })
      currentProject.value = data
    }
  }

  function clear() {
    currentProject.value = null
  }

  return {
    projects,
    currentProject,
    loading,
    currentStep,
    stepIndex,
    fetchProjects,
    fetchProject,
    nextStep,
    clear,
  }
})