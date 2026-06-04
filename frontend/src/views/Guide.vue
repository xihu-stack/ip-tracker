<template>
  <div>
    <h2 style="margin-bottom: 20px">使用说明</h2>

    <el-card style="margin-bottom: 16px">
      <template #header><b>系统简介</b></template>
      <p style="line-height: 1.8; margin: 0">
        本平台用于收集和管理员工电脑的公网 IP 地址，通过 IP 自动解析出所在城市并在地图上标注，方便 IT 管理人员了解员工电脑的网络接入位置。
      </p>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><b>页面功能</b></template>
      <el-table :data="pageList" stripe :show-header="false">
        <el-table-column width="140">
          <template #default="{ row }">
            <el-tag :type="row.tag" size="large">{{ row.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="desc" />
      </el-table>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><b>工作原理</b></template>
      <div style="line-height: 2">
        <el-steps direction="vertical" :active="5" finish-status="success">
          <el-step title="推送部署">
            <template #description>
              管理员通过 IP-guard 将 <el-tag size="small">deploy.ps1</el-tag> 推送到员工电脑，以 SYSTEM 身份静默执行
            </template>
          </el-step>
          <el-step title="安装常驻任务">
            <template #description>
              脚本在 <code>C:\ProgramData\Company_Network</code> 目录下写入上报脚本，并创建 SYSTEM 级计划任务，整个过程无需员工操作，完全无感知
            </template>
          </el-step>
          <el-step title="定时上报">
            <template #description>
              计划任务以 SYSTEM 身份运行，每 10 分钟执行一次，获取公网 IP 和经纬度后上报到服务器
            </template>
          </el-step>
          <el-step title="IP 解析">
            <template #description>
              服务器收到 IP 后，通过 ip-api.com 在线查询解析出省份、城市和经纬度信息
            </template>
          </el-step>
          <el-step title="管理查询">
            <template #description>
              管理员通过前台页面查看设备在线状态、地图分布、历史 IP 记录，并可编辑员工姓名
            </template>
          </el-step>
        </el-steps>
      </div>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><b>在线/离线判定逻辑</b></template>
      <el-table :data="statusList" stripe>
        <el-table-column label="状态" width="200">
          <template #default="{ row }">
            <el-tag :type="row.tag" effect="dark">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="condition" label="判定条件" />
        <el-table-column prop="meaning" label="说明" />
      </el-table>
      <el-alert type="info" :closable="false" style="margin-top: 12px" show-icon>
        <template #title>
          设备总数 = 在线 + 离线，互为补集。判定依据是员工电脑的上报时间戳（非主动探测）。电脑关机/断网后最多 10 分钟页面会显示离线。若员工已离职或已卸载脚本，可在员工列表中删除该设备。
        </template>
      </el-alert>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><b>部署步骤（IP-guard 推送）</b></template>
      <el-timeline>
        <el-timeline-item type="primary" :hollow="false">
          <b>确认配置</b>
          <p style="color: #909399; margin: 4px 0">打开 <code>deploy.ps1</code>，确认第 17 行的 <code>SERVER_URL</code> 为实际服务器地址</p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>创建软件包</b>
          <p style="color: #909399; margin: 4px 0">IP-guard 控制台 → 软件分发 → 新建软件包，分发模式选择 <b>执行程序</b></p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>添加文件</b>
          <p style="color: #909399; margin: 4px 0">点击新增，选择 <code>deploy.ps1</code></p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>设置命令行</b>
          <p style="color: #909399; margin: 4px 0">
            <code style="word-break: break-all">powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File deploy.ps1</code>
          </p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>运行模式</b>
          <p style="color: #909399; margin: 4px 0"><b>不勾选</b>"以当前登录用户身份运行"（以 SYSTEM 身份执行，权限更高）</p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>选择目标电脑 → 执行</b>
        </el-timeline-item>
        <el-timeline-item type="success" :hollow="false">
          <b>验证</b>
          <p style="color: #909399; margin: 4px 0">刷新前台页面，仪表盘或员工列表中出现新设备即为部署成功。在员工列表点击"编辑"可填写员工姓名。</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><b>卸载步骤（取消上报）</b></template>
      <el-timeline>
        <el-timeline-item type="danger" :hollow="false">
          <b>推送卸载脚本</b>
          <p style="color: #909399; margin: 4px 0">通过 IP-guard 推送 <code>uninstall.ps1</code>，命令行：<code>powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File uninstall.ps1</code>，同样不勾选"以当前登录用户身份运行"</p>
        </el-timeline-item>
        <el-timeline-item type="danger" :hollow="false">
          <b>卸载内容</b>
          <p style="color: #909399; margin: 4px 0">删除计划任务 <code>Company_IP_Tracker</code>、安装目录 <code>C:\ProgramData\Company_Network</code> 及所有日志文件</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><b>员工电脑上的文件</b></template>
      <el-table :data="fileList" stripe>
        <el-table-column prop="file" label="文件/任务" width="420" />
        <el-table-column prop="desc" label="说明" />
        <el-table-column prop="visible" label="员工可见" width="100">
          <template #default="{ row }">
            <el-tag :type="row.visible === '否' ? 'success' : 'danger'" size="small">{{ row.visible }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header><b>数据去重规则</b></template>
      <p style="line-height: 1.8; margin: 0; color: #606266">
        同一员工、同一 IP 地址，<b>1 小时内</b>不会重复记录。例如员工电脑每 10 分钟上报一次，
        如果 IP 没变，服务器只会记录一次，不会产生冗余数据。只有当 IP 发生变化（如切换网络、
        移动办公）时才会新增一条记录。
      </p>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const pageList = ref([
  { name: '仪表盘', tag: '', desc: '查看设备总数、在线数、离线数。下方中国地图展示设备分布位置（青色光点），鼠标悬停可查看城市和设备数量。在线和离线设备列表支持滚动查看。' },
  { name: '员工列表', tag: 'success', desc: '查看所有已部署的员工电脑，显示员工姓名、主机名、最新 IP、所在城市、最后上报时间和在线状态。支持按姓名或主机名搜索。可编辑员工姓名、查看历史记录，也可删除已离职或已卸载的员工设备。' },
  { name: 'IP 历史', tag: 'warning', desc: '选择某个员工，按日期范围查询该员工的所有 IP 上报记录，包括每次上报的时间和解析出的城市。' },
])

const statusList = ref([
  { status: '在线', tag: 'success', condition: '员工电脑最近 10 分钟内成功上报', meaning: '电脑开机、网络正常、计划任务正常运行' },
  { status: '离线', tag: 'warning', condition: '超过 10 分钟没有成功上报', meaning: '电脑关机、断网、计划任务异常或脚本被卸载' },
])

const fileList = ref([
  { file: 'C:\\ProgramData\\Company_Network\\', desc: '安装目录', visible: '否' },
  { file: '└ report.ps1', desc: 'IP 上报脚本', visible: '否' },
  { file: '计划任务: Company_IP_Tracker', desc: 'SYSTEM 级计划任务，每 10 分钟执行一次，开机即运行', visible: '否' },
])
</script>
