import { checkApiKey, checkConfig } from '../api/keyApi.js'
import { escapeHtml } from '../utils/format.js'
import {
  clearProviderConfig,
  normalizeProviderConfig,
  readProviderConfig,
  saveProviderConfig
} from '../utils/providerConfig.js'

export function SettingsPage() {
  return {
    html: `
      <section class="page page--narrow">
        <div class="page-heading"><div><p class="eyebrow">安全设置</p><h1>AI 服务配置</h1></div><span class="status status--done">仅会话保存</span></div>
        <div class="settings-block">
          <div class="settings-block__header">
            <div><p class="eyebrow">PROVIDER SESSION</p><h2>推荐接口</h2></div>
            <span id="provider-mode" class="status status--partial">BACKEND DEFAULT</span>
          </div>
          <p class="settings-intro">接入 OpenAI 兼容的 Chat Completions 服务。配置只保留在当前标签页会话中，关闭后自动失效。</p>
          <form id="provider-form" novalidate>
            <div class="provider-fields">
              <div class="provider-field">
                <label for="api-base-url">API 接口地址</label>
                <input id="api-base-url" name="apiBaseUrl" type="url" inputmode="url" autocomplete="url" spellcheck="false" aria-describedby="api-base-url-help" placeholder="https://api.openai.com/v1" />
                <p id="api-base-url-help" class="input-help">可填写服务的 /v1 地址或完整 /chat/completions 地址；留空时使用后端默认接口。</p>
              </div>
              <div class="provider-field">
                <label for="ai-model">模型</label>
                <input id="ai-model" name="model" type="text" autocomplete="off" spellcheck="false" aria-describedby="ai-model-help" placeholder="gpt-4o-mini" />
                <p id="ai-model-help" class="input-help">填写接口支持的模型标识；留空时使用后端默认模型。</p>
              </div>
              <div class="provider-field provider-field--wide">
                <label for="api-key">用户 API Key</label>
                <div class="secret-field">
                  <input id="api-key" name="apiKey" type="password" autocomplete="off" spellcheck="false" aria-describedby="api-key-help" placeholder="sk-..." />
                  <button id="api-key-toggle" class="secret-toggle" type="button" aria-label="显示 API Key" aria-pressed="false" title="显示 API Key">
                    <i class="secret-icon secret-icon--reveal" data-lucide="eye"></i>
                    <i class="secret-icon secret-icon--conceal" data-lucide="eye-off"></i>
                  </button>
                </div>
                <p id="api-key-help" class="input-help">Key 只通过请求头发送。保存时检查配置格式，不会测试账户权限、余额或实际调用结果。</p>
              </div>
            </div>
            <div class="actions provider-actions">
              <button id="provider-save" class="button" type="submit">
                <i class="button-icon button-icon--default" data-lucide="save"></i>
                <i class="button-icon button-icon--loading" data-lucide="loader-circle"></i>
                <span data-button-label>保存配置</span>
              </button>
              <button id="provider-clear" class="button button--danger" type="button"><i data-lucide="trash-2"></i>清除全部</button>
            </div>
            <div id="provider-status" class="form-status" role="status" aria-live="polite" aria-atomic="true"></div>
          </form>
        </div>
        <div class="section-divider"></div>
        <h2>运行状态</h2><div id="config-status" class="muted" aria-live="polite">正在检查...</div>
      </section>`,
    mount() {
      const form = document.querySelector('#provider-form')
      const apiKeyInput = document.querySelector('#api-key')
      const apiBaseUrlInput = document.querySelector('#api-base-url')
      const modelInput = document.querySelector('#ai-model')
      const toggleButton = document.querySelector('#api-key-toggle')
      const saveButton = document.querySelector('#provider-save')
      const clearButton = document.querySelector('#provider-clear')
      const status = document.querySelector('#provider-status')
      const modeBadge = document.querySelector('#provider-mode')
      const configContainer = document.querySelector('#config-status')
      const storedConfig = readProviderConfig()
      let userKeyAllowed = true
      let saving = false

      apiKeyInput.value = storedConfig.apiKey
      apiBaseUrlInput.value = storedConfig.apiBaseUrl
      modelInput.value = storedConfig.model

      function setStatus(kind, message) {
        status.className = `form-status${kind ? ` form-status--${kind}` : ''}`
        status.textContent = message
      }

      function setMode(hasUserConfig) {
        if (!userKeyAllowed) {
          modeBadge.className = 'status status--todo'
          modeBadge.textContent = 'USER KEY DISABLED'
          return
        }
        modeBadge.className = `status ${hasUserConfig ? 'status--done' : 'status--partial'}`
        modeBadge.textContent = hasUserConfig ? 'SESSION ACTIVE' : 'BACKEND DEFAULT'
      }

      function syncDisabledState() {
        const providerInputsDisabled = saving || !userKeyAllowed
        apiKeyInput.disabled = providerInputsDisabled
        apiBaseUrlInput.disabled = providerInputsDisabled
        modelInput.disabled = providerInputsDisabled
        toggleButton.disabled = providerInputsDisabled
        saveButton.disabled = providerInputsDisabled
        clearButton.disabled = saving
        form.setAttribute('aria-busy', String(saving))
        saveButton.classList.toggle('is-loading', saving)
        saveButton.querySelector('[data-button-label]').textContent = saving ? '正在检查格式...' : '保存配置'
      }

      function readFormConfig() {
        return normalizeProviderConfig({
          apiKey: apiKeyInput.value,
          apiBaseUrl: apiBaseUrlInput.value,
          model: modelInput.value
        })
      }

      function fillForm(config) {
        apiKeyInput.value = config.apiKey
        apiBaseUrlInput.value = config.apiBaseUrl
        modelInput.value = config.model
      }

      setMode(Boolean(storedConfig.apiKey))
      syncDisabledState()

      toggleButton.addEventListener('click', () => {
        const visible = apiKeyInput.type === 'text'
        apiKeyInput.type = visible ? 'password' : 'text'
        toggleButton.setAttribute('aria-pressed', String(!visible))
        toggleButton.setAttribute('aria-label', visible ? '显示 API Key' : '隐藏 API Key')
        toggleButton.title = visible ? '显示 API Key' : '隐藏 API Key'
        apiKeyInput.focus()
      })

      form.addEventListener('submit', async event => {
        event.preventDefault()
        const submittedConfig = readFormConfig()
        if (!submittedConfig.apiKey) {
          setStatus('error', '请输入用户 API Key；如需使用后端默认配置，请清除当前会话配置。')
          apiKeyInput.focus()
          return
        }
        if (submittedConfig.apiBaseUrl && !apiBaseUrlInput.validity.valid) {
          setStatus('error', 'API 接口地址格式不正确，请输入完整的 http:// 或 https:// 地址。')
          apiBaseUrlInput.focus()
          return
        }

        saving = true
        setStatus('info', '正在检查 Key、接口地址和模型格式...')
        syncDisabledState()
        try {
          const result = await checkApiKey(submittedConfig)
          const data = result?.data || {}
          if (data.allowUserApiKey === false) throw new Error('服务器当前不允许使用用户 API Key。')
          if (data.userKeyValid !== true || data.activeSource !== 'user') {
            throw new Error('API Key 格式不正确，请检查后重新输入。')
          }
          const savedConfig = saveProviderConfig({
            apiKey: submittedConfig.apiKey,
            apiBaseUrl: data.apiBaseUrl || submittedConfig.apiBaseUrl,
            model: data.model || submittedConfig.model
          })
          fillForm(savedConfig)
          setMode(true)
          setStatus('success', `格式检查通过，已保存 ${data.maskedUserKey || '用户 Key'} 的会话配置。`)
        } catch (error) {
          setStatus('error', error.message || '配置保存失败，请检查后重试。')
        } finally {
          saving = false
          syncDisabledState()
        }
      })

      clearButton.addEventListener('click', () => {
        clearProviderConfig()
        fillForm(normalizeProviderConfig())
        apiKeyInput.type = 'password'
        toggleButton.setAttribute('aria-pressed', 'false')
        toggleButton.setAttribute('aria-label', '显示 API Key')
        toggleButton.title = '显示 API Key'
        setMode(false)
        setStatus('success', '已清除当前会话中的 API Key、接口地址和模型。')
      })

      checkConfig()
        .then(result => {
          const data = result.data
          userKeyAllowed = data.allowUserApiKey !== false
          apiBaseUrlInput.placeholder = data.apiBaseUrl || 'https://api.openai.com/v1/chat/completions'
          modelInput.placeholder = data.model || 'gpt-4o-mini'
          syncDisabledState()
          setMode(Boolean(apiKeyInput.value.trim()))
          if (!userKeyAllowed) {
            setStatus('error', '服务器已禁用用户 API Key，当前只能使用后端默认配置。')
          }
          configContainer.innerHTML = `<div class="config-grid"><span>默认接口 <strong>${escapeHtml(data.apiBaseUrl || '未配置')}</strong></span><span>默认模型 <strong>${escapeHtml(data.model || '未配置')}</strong></span><span>默认 AI Key <strong>${data.aiConfigured ? '已配置' : '未配置'}</strong></span><span>用户 Key <strong>${userKeyAllowed ? '允许' : '禁用'}</strong></span><span>游戏数据 <strong>${Number(data.gamesCount) || 0} 条</strong></span><span>环境 <strong>${escapeHtml(data.environment)}</strong></span></div>`
        })
        .catch(error => {
          configContainer.textContent = error.message
        })
    }
  }
}
