<template>
  <div v-if="image" class="fullscreen-viewer">
    <img 
      :src="image.filePath" 
      :alt="image.name" 
      class="fullscreen-image"
      :style="{ cursor: calibratingScale ? 'crosshair' : 'default' }"
      @click="onImageClick"
    />
    
    <!-- 右侧工具栏 -->
    <div class="toolbar">
      <button class="info-btn" @click="showInfo = !showInfo" title="图片信息">ⓘ</button>
      <button 
        class="calibrate-btn" 
        :class="{ active: calibratingScale }"
        @click="toggleCalibration"
        title="校准比例尺"
      >
        📏
      </button>
    </div>

    <!-- 图片信息 -->
    <div v-if="showInfo" class="image-info">
      <h3>{{ image.name }}</h3>
      <p>{{ formatDate(image.createdAt) }}</p>
    </div>

    <!-- 校准状态 -->
    <div v-if="calibratingScale" class="calibration-status">
      <p>点击图片上的两个点来定义比例尺</p>
      <p v-if="calibrationPoints.length > 0">已选择 {{ calibrationPoints.length }}/2 个点</p>
      <div v-if="calibrationPoints.length === 2" class="distance-input">
        <label>两点间实际距离 (m):</label>
        <input 
          v-model.number="actualDistance" 
          type="number" 
          placeholder="输入距离"
          @keyup.enter="confirmCalibration"
        />
        <button @click="confirmCalibration">确认</button>
        <button @click="cancelCalibration" class="cancel-btn">取消</button>
      </div>
    </div>

    <!-- 左下角比例尺显示 -->
    <div v-if="scaleInfo" class="scale-display">
      <div class="scale-bar">
        <div class="bar" :style="{ width: scaleInfo.barWidth + 'px' }"></div>
      </div>
      <p>{{ scaleInfo.text }}</p>
    </div>

    <!-- 校准点标记 -->
    <svg v-if="calibrationPoints.length > 0" class="calibration-overlay">
      <circle 
        v-for="(point, idx) in calibrationPoints" 
        :key="idx"
        :cx="point.x" 
        :cy="point.y" 
        r="5" 
        class="calibration-point"
      />
      <line 
        v-if="calibrationPoints.length === 2"
        :x1="calibrationPoints[0].x"
        :y1="calibrationPoints[0].y"
        :x2="calibrationPoints[1].x"
        :y2="calibrationPoints[1].y"
        class="calibration-line"
      />
    </svg>
  </div>
  <div v-else class="error-screen">
    <p>No image data available</p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../services/api'

const image = ref(null)
const showInfo = ref(false)
const calibratingScale = ref(false)
const calibrationPoints = ref([])
const actualDistance = ref('')
const imageElement = ref(null)
const scaleInfo = ref(null)
const isSaving = ref(false)

const formatDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleString()
  } catch (_e) {
    return dateString
  }
}

onMounted(async () => {
  // Retrieve image data from sessionStorage
  const data = sessionStorage.getItem('imageViewerData')
  if (data) {
    try {
      image.value = JSON.parse(data)
      
      // 尝试从数据库加载比例尺
      if (image.value && image.value.id && image.value.pixelsPerMeter) {
        try {
          const scaleData = JSON.parse(image.value.pixelsPerMeter)
          generateScaleDisplay(scaleData)
        } catch (e) {
          console.error('Failed to parse pixelsPerMeter from database:', e)
        }
      } else {
        // 如果数据库没有，尝试从 sessionStorage 恢复
        const savedScale = sessionStorage.getItem('imageScale')
        if (savedScale) {
          const scale = JSON.parse(savedScale)
          generateScaleDisplay(scale)
        }
      }
    } catch (e) {
      console.error('Failed to parse image data:', e)
    }
  }
})

const toggleCalibration = () => {
  if (calibratingScale.value) {
    // 取消校准
    cancelCalibration()
  } else {
    // 开始校准
    calibratingScale.value = true
    calibrationPoints.value = []
    actualDistance.value = ''
  }
}

const onImageClick = (event) => {
  if (!calibratingScale.value) return

  const img = event.target
  const rect = img.getBoundingClientRect()
  
  // 获取相对于图片左上角的点击坐标
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  if (calibrationPoints.value.length < 2) {
    calibrationPoints.value.push({ x, y })
  }
}

const confirmCalibration = async () => {
  if (calibrationPoints.value.length !== 2 || !actualDistance.value) {
    alert('请选择两个点并输入距离')
    return
  }

  // 计算像素距离
  const p1 = calibrationPoints.value[0]
  const p2 = calibrationPoints.value[1]
  const pixelDistance = Math.sqrt(
    Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2)
  )

  // 计算像素/米的比例
  const scale = {
    pixelsPerMeter: pixelDistance / actualDistance.value,
    actualDistance: actualDistance.value,
    pixelDistance: pixelDistance
  }

  // 保存到数据库
  if (image.value && image.value.id) {
    isSaving.value = true
    try {
      await api.post(`/drawings/${image.value.id}/calibrate-scale`, scale)
      console.log('Scale calibration saved to database')
    } catch (error) {
      console.error('Failed to save scale calibration:', error)
      alert('保存比例尺失败，但本地已保存')
    } finally {
      isSaving.value = false
    }
  }

  // 保存到 sessionStorage
  sessionStorage.setItem('imageScale', JSON.stringify(scale))

  generateScaleDisplay(scale)
  calibratingScale.value = false
  calibrationPoints.value = []
  actualDistance.value = ''
}

const cancelCalibration = () => {
  calibratingScale.value = false
  calibrationPoints.value = []
  actualDistance.value = ''
}

const generateScaleDisplay = (scale) => {
  // 生成 100px 对应的实际距离
  const barWidthPx = 100
  const actualLen = (barWidthPx / scale.pixelsPerMeter).toFixed(2)
  
  scaleInfo.value = {
    barWidth: barWidthPx,
    text: `${actualLen} m`
  }
}
</script>

<style scoped>
.fullscreen-viewer {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  overflow: auto;
  width: 100%;
  height: 100%;
}

.fullscreen-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
}

.toolbar {
  position: fixed;
  top: 1rem;
  right: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 10001;
}

.info-btn,
.calibrate-btn {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: rgba(100, 181, 246, 0.2);
  color: #64b5f6;
  border: 1px solid rgba(100, 181, 246, 0.4);
  font-size: 1.2rem;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-btn:hover,
.calibrate-btn:hover {
  background: rgba(100, 181, 246, 0.3);
  transform: scale(1.1);
}

.calibrate-btn.active {
  background: rgba(76, 175, 80, 0.3);
  color: #4caf50;
  border-color: rgba(76, 175, 80, 0.5);
}

.image-info {
  position: fixed;
  top: 4rem;
  right: 1rem;
  color: #fff;
  background: rgba(0, 0, 0, 0.8);
  padding: 1rem 1.5rem;
  border-radius: 8px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  z-index: 10002;
  min-width: 250px;
}

.image-info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #64b5f6;
  word-break: break-word;
}

.image-info p {
  margin: 0;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.calibration-status {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.9);
  border: 2px solid rgba(76, 175, 80, 0.5);
  padding: 2rem;
  border-radius: 12px;
  z-index: 10003;
  text-align: center;
  color: #fff;
  min-width: 300px;
}

.calibration-status p {
  margin: 0.5rem 0;
  font-size: 1rem;
}

.distance-input {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.distance-input label {
  font-size: 0.9rem;
  color: #64b5f6;
}

.distance-input input {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(100, 181, 246, 0.3);
  color: #fff;
  border-radius: 6px;
  font-size: 1rem;
}

.distance-input input:focus {
  outline: none;
  border-color: #64b5f6;
  background: rgba(100, 181, 246, 0.1);
}

.distance-input button {
  padding: 0.75rem 1rem;
  background: #4caf50;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

.distance-input button:hover {
  background: #45a049;
}

.distance-input button.cancel-btn {
  background: #f44336;
}

.distance-input button.cancel-btn:hover {
  background: #da190b;
}

.scale-display {
  position: fixed;
  bottom: 1rem;
  left: 1rem;
  background: rgba(0, 0, 0, 0.7);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(76, 175, 80, 0.3);
  z-index: 10002;
  min-width: 150px;
}

.scale-bar {
  height: 3px;
  background: #4caf50;
  border-radius: 2px;
  margin-bottom: 0.5rem;
  width: 100px;
}

.scale-bar .bar {
  height: 100%;
  background: #4caf50;
  border-radius: 2px;
}

.scale-display p {
  margin: 0;
  color: #fff;
  font-size: 0.875rem;
  text-align: center;
}

.calibration-overlay {
  position: fixed;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
  pointer-events: none;
}

.calibration-point {
  fill: #4caf50;
  stroke: #fff;
  stroke-width: 2;
}

.calibration-line {
  stroke: #4caf50;
  stroke-width: 2;
  stroke-dasharray: 5,5;
}

.error-screen {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.2rem;
  z-index: 10000;
}
</style>
