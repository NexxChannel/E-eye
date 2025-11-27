<template>
  <div class="card projects-card">
    <h2>Projects</h2>
    
    <!-- Create Project Form -->
    <form @submit.prevent="createProject" class="create-form">
      <div class="form-group">
        <label>Project Name</label>
        <input v-model="newProjectName" type="text" required placeholder="Enter project name" />
      </div>
      <button type="submit" :disabled="loading || !newProjectName.trim()">
        {{ loading ? 'Creating...' : 'Create Project' }}
      </button>
    </form>

    <p v-if="message" :class="['message', isError ? 'error' : 'success']">{{ message }}</p>

    <!-- Projects List -->
    <div class="projects-list" v-if="projects.length > 0">
      <h3>Your Projects</h3>
      <ul>
        <li v-for="project in projects" :key="project.id" class="project-item">
          <div class="left" @click="viewProject(project.id)">
            <span class="project-name">{{ project.name }}</span>
            <span class="project-date">{{ formatDate(project.createdAt) }}</span>
          </div>
          <div class="right">
            <button class="delete-btn" @click.stop.prevent="deleteProject(project.id)">Delete</button>
          </div>
        </li>
      </ul>
    </div>
    <p v-else-if="!loading && hasFetched" class="no-projects">No projects yet. Create one above!</p>

    <!-- Project Detail Modal -->
    <div v-if="selectedProject" class="project-detail">
      <h3>Project Details</h3>
      <button class="close-btn" @click="selectedProject = null">&times;</button>
      <table class="project-table">
        <tbody>
          <tr><th>Name</th><td>{{ selectedProject.name }}</td></tr>
          <tr><th>ID</th><td>{{ selectedProject.id }}</td></tr>
          <tr><th>Owner</th><td>{{ ownerEmail }}</td></tr>
          <tr><th>Created At</th><td>{{ formatFullDate(selectedProject.createdAt) }}</td></tr>
        </tbody>
      </table>
      <div class="drawings-list" v-if="drawings.length">
        <h4>Your Drawings</h4>
        <ul>
          <li v-for="d in drawings" :key="d.id" class="drawing-item">
            <div class="left">
              <span class="drawing-name" @click="openPreview(d)">{{ d.name }}</span>
              <span class="drawing-date">{{ formatDate(d.createdAt) }}</span>
            </div>
            <div class="right">
              <button class="open-btn" @click.stop="openDrawingFullscreen(d)">Open</button>
              <button class="preview-btn" @click.stop="openPreview(d)">Preview</button>
              <button class="delete-btn" @click.stop="deleteDrawing(d.id)">Delete</button>
            </div>
          </li>
        </ul>
      </div>
        <div class="upload-area">
          <label class="upload-label">Create Drawing</label>
          <div class="form-row">
            <input v-model="newDrawingName" type="text" placeholder="Drawing name" />
            <input type="file" ref="fileInput" accept="image/png, image/jpeg" @change="onFileChange" />
            <button :disabled="!selectedFile || uploading || !newDrawingName.trim()" @click="uploadFile">Create</button>
          </div>
          <div v-if="uploading" class="progress">Uploading... {{ uploadProgress }}%</div>
        </div>
    </div>

    <div v-if="previewDrawing" class="image-modal">
      <div class="image-container">
        <button class="close-btn" @click="previewDrawing = null">&times;</button>
        <img :src="previewDrawing.filePath" :alt="previewDrawing.name" />
        <p class="caption">{{ previewDrawing.name }} — {{ formatFullDate(previewDrawing.createdAt) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../services/api'

const props = defineProps({
  token: String
})

const emit = defineEmits(['open-image'])

const newProjectName = ref('')
const projects = ref([])
const selectedProject = ref(null)
const ownerEmail = ref('')
const drawings = ref([])
const previewDrawing = ref(null)
const message = ref('')
const isError = ref(false)
const loading = ref(false)
const hasFetched = ref(false)

const getAuthHeaders = () => ({
  headers: { 'Authorization': `Bearer ${props.token}` }
})

const fetchProjects = async () => {
  if (!props.token) return
  
  loading.value = true
  try {
    const response = await api.get('/projects', getAuthHeaders())
    let projectsData = response.data || []
    // sort by createdAt desc (newest first)
    projectsData.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    projects.value = projectsData
    hasFetched.value = true
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  } finally {
    loading.value = false
  }
}

const createProject = async () => {
  console.log('createProject called, token:', props.token ? 'exists' : 'missing')
  
  if (!props.token) {
    isError.value = true
    message.value = 'Please login first to create projects'
    return
  }
  
  if (!newProjectName.value.trim()) {
    isError.value = true
    message.value = 'Project name is required'
    return
  }
  
  loading.value = true
  message.value = ''
  isError.value = false
  
  try {
    console.log('Sending request to /projects/create')
    const response = await api.post('/projects/create', 
      { name: newProjectName.value.trim() },
      getAuthHeaders()
    )
    console.log('Response:', response.data)
    message.value = `Project "${response.data.name}" created!`
    newProjectName.value = ''
    await fetchProjects()
  } catch (error) {
    console.error('Create project error:', error)
    isError.value = true
    message.value = error.response?.data?.detail || error.message || 'Failed to create project'
  } finally {
    loading.value = false
  }
}

// upload helpers
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const newDrawingName = ref('')
const fileInput = ref(null)

const onFileChange = (e) => {
  const f = e.target.files && e.target.files[0]
  if (f) selectedFile.value = f
}

const uploadFile = async () => {
  if (!selectedFile.value || !selectedProject.value) return
  uploading.value = true
  uploadProgress.value = 0
  try {
  const form = new FormData()
  form.append('file', selectedFile.value)
  form.append('name', newDrawingName.value || '')
    const resp = await api.post(`/projects/${selectedProject.value.id}/drawings/upload`, form, {
      headers: {
        'Authorization': `Bearer ${props.token}`,
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (ev) => {
        if (ev.total) uploadProgress.value = Math.round((ev.loaded / ev.total) * 100)
      }
    })
    // refresh drawings
    const dresp = await api.get(`/projects/${selectedProject.value.id}/drawings`, getAuthHeaders())
    // convert backend-relative filePath to absolute URL using api baseURL
    const raw = dresp.data || []
    const mapped = raw.map(d => ({
      ...d,
      filePath: d.filePath && d.filePath.startsWith('/') ? `${api.defaults.baseURL.replace(/\/$/, '')}${d.filePath}` : d.filePath
    }))
    drawings.value = mapped
  selectedFile.value = null
  newDrawingName.value = ''
  // clear native file input
  try { if (fileInput.value) fileInput.value.value = null } catch(_){}
    uploadProgress.value = 100
  } catch (e) {
    console.error('Upload failed', e)
    isError.value = true
    message.value = e.response?.data?.detail || 'Upload failed'
  } finally {
    uploading.value = false
    setTimeout(() => (uploadProgress.value = 0), 800)
  }
}

const deleteDrawing = async (drawingId) => {
  if (!confirm('Delete this drawing?')) return
  try {
    await api.delete(`/drawings/${drawingId}`, getAuthHeaders())
    drawings.value = drawings.value.filter(d => d.id !== drawingId)
  } catch (e) {
    console.error('Delete drawing failed', e)
    isError.value = true
    message.value = e.response?.data?.detail || 'Failed to delete drawing'
  }
}

const deleteProject = async (projectId) => {
  if (!confirm('Delete this project and all its drawings?')) return
  try {
    await api.delete(`/projects/${projectId}`, getAuthHeaders())
    // remove from local list
    projects.value = projects.value.filter(p => p.id !== projectId)
    // if the deleted project is currently selected, close the detail view
    if (selectedProject.value && selectedProject.value.id === projectId) {
      selectedProject.value = null
      drawings.value = []
    }
  } catch (e) {
    console.error('Delete project failed', e)
    isError.value = true
    message.value = e.response?.data?.detail || 'Failed to delete project'
  }
}

const viewProject = async (projectId) => {
  if (!props.token) return
  try {
    const response = await api.get(`/projects/${projectId}`, getAuthHeaders())
    selectedProject.value = response.data
    // fetch user info for email
    try {
      const userResp = await api.get('/me', getAuthHeaders())
      ownerEmail.value = userResp.data.email || userResp.data.id || ''
    } catch (e) {
      ownerEmail.value = selectedProject.value.ownerId
    }
    // fetch drawings for this project
    try {
      const dresp = await api.get(`/projects/${projectId}/drawings`, getAuthHeaders())
      const raw = dresp.data || []
      const mapped = raw.map(d => ({
        ...d,
        filePath: d.filePath && d.filePath.startsWith('/') ? `${api.defaults.baseURL.replace(/\/$/, '')}${d.filePath}` : d.filePath
      }))
      drawings.value = mapped
      // ensure sorted by createdAt desc
      drawings.value.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    } catch (e) {
      drawings.value = []
    }
  } catch (error) {
    isError.value = true
    message.value = error.response?.data?.detail || 'Failed to load project'
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}
const formatFullDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleString()
  } catch (_e) {
    return dateString
  }
}

const openPreview = (d) => {
  console.log('📸 openPreview called with drawing:', d)
  if (!d || !d.filePath) {
    console.warn('Drawing missing or no filePath:', d)
    return
  }
  // resolve file path to absolute URL
  let filePath = d.filePath
  if (filePath.startsWith('/')) {
    const base = api.defaults?.baseURL || 'http://localhost:8000'
    filePath = `${base.replace(/\/$/, '')}${filePath}`
  }
  console.log('📸 resolved filePath:', filePath)
  previewDrawing.value = { ...d, filePath }
  console.log('📸 previewDrawing set:', previewDrawing.value)
}

const openDrawingFullscreen = (d) => {
  console.log('🖼️ openDrawingFullscreen called with drawing:', d)
  if (!d || !d.filePath) {
    console.warn('Drawing missing or no filePath:', d)
    return
  }
  // resolve file path to absolute URL
  let filePath = d.filePath
  if (filePath.startsWith('/')) {
    const base = api.defaults?.baseURL || 'http://localhost:8000'
    filePath = `${base.replace(/\/$/, '')}${filePath}`
  }
  console.log('🖼️ resolved filePath:', filePath)
  // emit to parent to open fullscreen viewer
  emit('open-image', { ...d, filePath })
}

watch(() => props.token, (newToken) => {
  if (newToken) {
    fetchProjects()
  } else {
    projects.value = []
    hasFetched.value = false
  }
})

onMounted(() => {
  if (props.token) {
    fetchProjects()
  }
})
</script>

<style scoped>
.card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  padding: 2rem;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  max-width: 720px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.projects-card {
  position: relative;
}

h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  background: linear-gradient(to right, #fff, #aaa);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #eee;
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
}

.project-item .left { cursor: pointer; display:flex; gap:0.5rem; align-items:center }
.project-item .right { display:flex; align-items:center }
.form-row { display: flex; gap: 0.5rem; align-items: center; }
.form-row input[type="text"] { flex: 1 1 auto; }
.form-row input[type="file"] { flex: 0 0 auto; }

label {
  font-size: 0.875rem;
  color: #aaa;
}

input {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.75rem;
  border-radius: 8px;
  color: white;
  font-size: 1rem;
  transition: all 0.2s;
}

input:focus {
  outline: none;
  border-color: #646cff;
  background: rgba(0, 0, 0, 0.4);
}

button {
  background: #646cff;
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #535bf2;
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.message {
  font-size: 0.875rem;
  margin: 0;
  padding: 0.5rem;
  border-radius: 4px;
}

.success {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

.error {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

.projects-list {
  text-align: left;
}

.projects-list ul {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
}

.project-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
}

.project-item:hover {
  background: rgba(0, 0, 0, 0.4);
}

.project-name {
  font-weight: 500;
  color: #fff;
}

.project-date {
  font-size: 0.75rem;
  color: #888;
}

.no-projects {
  color: #888;
  font-size: 0.875rem;
  text-align: center;
}

.project-detail {
  position: relative;
  background: rgba(0, 0, 0, 0.3);
  padding: 1rem;
  border-radius: 8px;
  text-align: left;
}

.project-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.5rem;
}
.project-table th {
  text-align: left;
  vertical-align: top;
  padding: 0.25rem 0.5rem 0.25rem 0;
  color: #ccc;
  width: 35%;
}
.project-table td {
  padding: 0.25rem 0.5rem;
  color: #fff;
}

.close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: transparent;
  border: none;
  color: #888;
  font-size: 1.25rem;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
}

.close-btn:hover {
  color: #fff;
  background: transparent;
}

.drawings-list {
  margin-top: 1rem;
}
.drawings-list ul {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
}
.drawing-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: rgba(0,0,0,0.15);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  gap: 0.5rem;
}
.drawing-item .left {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}
.drawing-item .drawing-name {
  font-weight: 500;
  color: #fff;
  cursor: pointer;
  word-break: break-word;
}
.drawing-item .drawing-date {
  font-size: 0.75rem;
  color: #888;
}
.drawing-item .right {
  flex: 0 0 auto;
  display: flex;
  gap: 0.25rem;
  align-items: center;
}
.drawing-item:hover { background: rgba(0,0,0,0.25); }
.form-row { display: flex; gap: 0.5rem; align-items: center; }
.form-row input[type="file"] { padding: 0.25rem; }
.open-btn { background: transparent; color: #4caf50; border: 1px solid rgba(76,175,80,0.15); padding: 0.25rem 0.5rem; border-radius: 6px; }
.open-btn:hover { background: rgba(76,175,80,0.08); }
.preview-btn { background: transparent; color: #64b5f6; border: 1px solid rgba(100,181,246,0.15); padding: 0.25rem 0.5rem; border-radius: 6px; }
.preview-btn:hover { background: rgba(100,181,246,0.08); }
.delete-btn { background: transparent; color: #ff6b6b; border: 1px solid rgba(255,107,107,0.15); padding: 0.25rem 0.5rem; border-radius: 6px; }
.delete-btn:hover { background: rgba(255,107,107,0.08); }
.image-modal {
  position: fixed;
  left: 0; top: 0; right: 0; bottom: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.6);
  z-index: 9999;
}
.image-container {
  background: rgba(0,0,0,0.4);
  padding: 1rem;
  border-radius: 12px;
  max-width: 90%;
  max-height: 90%;
}
.image-container img {
  max-width: 100%;
  max-height: 70vh;
  display: block;
  margin: 0 auto;
}
.caption { color: #ddd; text-align: center; margin-top: 0.5rem; }
</style>
