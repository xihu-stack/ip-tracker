import { createApp } from 'vue'

// 注：不要在这里 import dayjs 或其插件——element-plus 内部自带 dayjs 并自行注册所需插件，
// 外部再引入会形成第二个 dayjs 实例，导致日期选择器报 "hour is not a function"。
// 中文语言包通过 Element Plus 官方 locale 提供。
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, { locale: zhCn })
app.use(router)
app.mount('#app')
