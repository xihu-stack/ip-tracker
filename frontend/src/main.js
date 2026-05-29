import { createApp } from 'vue'
import dayjs from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'
import advancedFormat from 'dayjs/plugin/advancedFormat'
import localeData from 'dayjs/plugin/localeData'
import weekOfYear from 'dayjs/plugin/weekOfYear'
import weekYear from 'dayjs/plugin/weekYear'
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter'
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore'
import 'dayjs/locale/zh-cn'

dayjs.extend(customParseFormat)
dayjs.extend(advancedFormat)
dayjs.extend(localeData)
dayjs.extend(weekOfYear)
dayjs.extend(weekYear)
dayjs.extend(isSameOrAfter)
dayjs.extend(isSameOrBefore)
dayjs.locale('zh-cn')

import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, { locale: { el: { pagination: { goto: '前往', pagesize: '条/页', total: '共 {total} 条', pageClassifier: '页' } } } })
app.use(router)
app.mount('#app')
