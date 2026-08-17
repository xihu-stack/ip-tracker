<template>
  <div>
    <div class="page-header">
      <div>
        <h2>使用说明</h2>
        <p class="page-sub">平台功能 · 部署流程 · 服务器运维手册</p>
      </div>
    </div>

    <el-card style="margin-bottom: 16px">
      <template #header><b>系统简介</b></template>
      <p class="guide-text">
        本平台用于收集和管理员工电脑的公网 IP 地址，通过 IP 自动解析出所在城市（支持精确到区级）并在地图上标注，方便 IT 管理人员了解员工电脑的网络接入位置。
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
        <el-table-column>
          <template #default="{ row }">
            <span class="guide-text">{{ row.desc }}</span>
          </template>
        </el-table-column>
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
              服务器收到 IP 后，通过 cip.cc 在线查询解析出省份和城市（cip.cc 限流时自动切换 pconline 备用源），经纬度由内置的中国城市坐标表给出
            </template>
          </el-step>
          <el-step title="管理查询">
            <template #description>
              管理员通过前台页面查看设备在线状态、地图分布、历史 IP 记录，并可编辑员工姓名或删除已离职员工
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
          设备总数 = 在线 + 离线，互为补集。判定依据是员工电脑的上报时间戳（非主动探测）。电脑关机/断网后最多 20 分钟页面会显示离线。若员工已离职或已卸载脚本，可在员工列表中删除该设备。
        </template>
      </el-alert>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><b>部署步骤（IP-guard 推送）</b></template>
      <el-timeline>
        <el-timeline-item type="primary" :hollow="false">
          <b>确认配置</b>
          <p class="step-desc">打开 <code>deploy.ps1</code>，确认第 17 行的 <code>SERVER_URL</code> 为实际服务器地址</p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>创建软件包</b>
          <p class="step-desc">IP-guard 控制台 → 软件分发 → 新建软件包，分发模式选择 <b>执行程序</b></p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>添加文件</b>
          <p class="step-desc">点击新增，选择 <code>deploy.ps1</code></p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>设置命令行</b>
          <p class="step-desc">
            <code style="word-break: break-all">powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File deploy.ps1</code>
          </p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>运行模式</b>
          <p class="step-desc"><b>不勾选</b>"以当前登录用户身份运行"（以 SYSTEM 身份执行，权限更高）</p>
        </el-timeline-item>
        <el-timeline-item type="primary" :hollow="false">
          <b>选择目标电脑 → 执行</b>
        </el-timeline-item>
        <el-timeline-item type="success" :hollow="false">
          <b>验证</b>
          <p class="step-desc">刷新前台页面，仪表盘或员工列表中出现新设备即为部署成功。在员工列表点击"编辑"可填写员工姓名。</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><b>卸载步骤（取消上报）</b></template>
      <el-timeline>
        <el-timeline-item type="danger" :hollow="false">
          <b>推送卸载脚本</b>
          <p class="step-desc">通过 IP-guard 推送 <code>clean_all_fixed.bat</code>，命令行：<code>powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File clean_all_fixed.bat</code>，同样不勾选"以当前登录用户身份运行"</p>
        </el-timeline-item>
        <el-timeline-item type="danger" :hollow="false">
          <b>卸载内容</b>
          <p class="step-desc">删除计划任务 <code>Company_IP_Tracker</code>、安装目录 <code>C:\ProgramData\Company_Network</code> 及所有日志文件</p>
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

    <el-card style="margin-bottom: 16px">
      <template #header><b>数据去重规则</b></template>
      <p class="guide-text">
        同一员工、同一 IP 地址，<b>1 小时内</b>不会重复记录。例如员工电脑每 10 分钟上报一次，
        如果 IP 没变，服务器只会记录一次，不会产生冗余数据。只有当 IP 发生变化（如切换网络、
        移动办公）时才会新增一条记录。
      </p>
    </el-card>

    <el-card>
      <template #header><b>服务器运维手册（管理员）</b></template>
      <el-collapse>
        <el-collapse-item title="① 更新最新代码" name="update">
          <p class="step-desc">在服务器上执行三条命令即可升级（前端构建产物随仓库提交，无需在服务器上构建）：</p>
          <pre class="cmd">cd /opt/ip-tracker
git pull
sudo systemctl restart ip-tracker</pre>
          <p class="step-desc">
            验证：<code>systemctl status ip-tracker</code> 为 active、<code>journalctl -u ip-tracker -n 20</code> 无报错；
            浏览器 <b>Ctrl+F5</b> 强刷避免旧缓存。升级不影响数据库数据，结构变更在启动时自动完成。
          </p>
        </el-collapse-item>
        <el-collapse-item title="② 服务管理" name="service">
          <pre class="cmd">systemctl status ip-tracker      # 查看状态
systemctl restart ip-tracker     # 重启
systemctl stop ip-tracker        # 停止
journalctl -u ip-tracker -f      # 实时日志</pre>
        </el-collapse-item>
        <el-collapse-item title="③ 忘记密码：命令行重置" name="password">
          <p class="step-desc">在 <code>/opt/ip-tracker</code> 目录下执行（把 <code>NewPass@123</code> 换成新密码）：</p>
          <pre class="cmd">venv/bin/python - &lt;&lt;'EOF'
import sys
sys.path.insert(0, 'server')
from auth import hash_password
from database import SessionLocal
from models import Admin

db = SessionLocal()
a = db.query(Admin).filter_by(username='admin').first()
if not a:
    a = Admin(username='admin', hashed_password='')
    db.add(a)
a.hashed_password = hash_password('NewPass@123')
db.commit()
print('密码已重置')
EOF</pre>
          <p class="step-desc">注意：必须在 /opt/ip-tracker 目录运行，数据库是相对路径，换目录会新建空库。</p>
        </el-collapse-item>
        <el-collapse-item title="④ 数据备份与恢复" name="backup">
          <p class="step-desc">全部业务数据都在一个 SQLite 文件里，备份它就备份了一切（在线备份，不必停服务）：</p>
          <pre class="cmd">sqlite3 /opt/ip-tracker/ip_tracker.db ".backup /root/backup/ip_tracker_$(date +%F).db"</pre>
          <p class="step-desc">
            恢复：先 <code>systemctl stop ip-tracker</code>，用备份文件覆盖 <code>/opt/ip-tracker/ip_tracker.db</code>，再 start。
            建议 crontab 配置每日自动备份，完整命令见仓库 docs/运维手册.md。
          </p>
        </el-collapse-item>
        <el-collapse-item title="⑤ 常见问题排查" name="trouble">
          <el-table :data="troubleList" stripe size="small">
            <el-table-column prop="issue" label="现象" width="170" />
            <el-table-column prop="fix" label="处理方法" />
          </el-table>
        </el-collapse-item>
      </el-collapse>
      <el-alert type="info" :closable="false" style="margin-top: 12px" show-icon>
        <template #title>
          完整运维手册（含防火墙放行、安全加固清单、客户端排障、API 速查）见仓库 docs/运维手册.md
        </template>
      </el-alert>
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
  { status: '在线', tag: 'success', condition: '员工电脑最近 20 分钟内成功上报', meaning: '电脑开机、网络正常、计划任务正常运行' },
  { status: '离线', tag: 'warning', condition: '超过 20 分钟没有成功上报', meaning: '电脑关机、断网、计划任务异常或脚本被卸载' },
])

const fileList = ref([
  { file: 'C:\\ProgramData\\Company_Network\\', desc: '安装目录', visible: '否' },
  { file: '└ report.ps1', desc: 'IP 上报脚本', visible: '否' },
  { file: '计划任务: Company_IP_Tracker', desc: 'SYSTEM 级计划任务，每 10 分钟执行一次，开机即运行', visible: '否' },
])

const troubleList = ref([
  { issue: '后台打不开', fix: 'systemctl status ip-tracker 查状态；起不来查 journalctl -u ip-tracker -n 50；服务正常则检查防火墙是否放行 8000' },
  { issue: '设备显示离线', fix: '在线阈值 20 分钟。终端执行 schtasks /query /TN "Company_IP_Tracker" 查计划任务是否在跑，或手动运行 report.ps1 测试上报' },
  { issue: '上报返回 403', fix: '客户端上报地址必须走 9000 端口且以 /api/report 结尾，检查 deploy.ps1 里的 SERVER_URL' },
  { issue: '归属地异常/未知', fix: 'cip.cc 限流时自动切 pconline 备用源，稍后自动恢复；历史数据可在服务器运行 server/cleanup_geo.py 批量修正' },
  { issue: '改了前端不生效', fix: '前端是构建产物，改 src 后必须在开发机 npm run build 并提交 dist；浏览器 Ctrl+F5 清缓存' },
])
</script>

<style scoped>
.guide-text {
  line-height: 1.8;
  margin: 0;
  color: #475569;
}
.step-desc {
  color: #909399;
  margin: 4px 0;
}
.cmd {
  background: #f0f6ff;
  border: 1px solid #d8e6f8;
  border-radius: 6px;
  padding: 12px 16px;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 12.5px;
  color: #1a3a5c;
  line-height: 1.7;
  overflow-x: auto;
  margin: 8px 0 12px;
}
</style>
