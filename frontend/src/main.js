import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import ImageViewerPage from './components/ImageViewerPage.vue'

const path = window.location.pathname

let component
if (path === '/image-viewer' || path.startsWith('/image-viewer')) {
  component = ImageViewerPage
} else {
  component = App
}

createApp(component).mount('#app')
