import React from 'react';
import { createRoot } from 'react-dom/client';
import {
  Download,
  FileAudio,
  FileVideo,
  Link,
  Loader2,
  Mic2,
  Play,
  RefreshCcw,
  Save,
  Square,
  UploadCloud,
} from 'lucide-react';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

const i18n = {
  zh: {
    appTitle: '本地视频翻译配音',
    appSubtitle: '上传文件或粘贴 YouTube 地址，按需下载、识别字幕、翻译、配音并合成视频。',
    ready: '环境就绪',
    setupNeeded: '环境待配置',
    settings: '任务设置',
    expandSettings: '展开设置',
    collapseSettings: '收起设置',
    resetSettings: '清除保存设置',
    localFile: '本地文件',
    chooseMedia: '选择音频或视频',
    youtube: 'YouTube',
    youtubeUrl: 'YouTube 视频地址',
    pipelineStep: '处理到哪一步',
    sourceLanguage: '源语言',
    targetLanguage: '目标语言',
    translationEngine: '翻译引擎',
    googleTranslate: 'Google 翻译',
    openaiTranslate: 'ChatGPT / OpenAI 兼容 API',
    model: '模型',
    whisperModel: 'Whisper 模型',
    ttsEngine: '配音引擎',
    ttsAuto: '自动，Edge 失败后本地兜底',
    ttsLocal: '本地 SAPI 离线',
    ttsEdge: 'Edge-TTS 在线',
    edgeVoice: 'Edge-TTS 声音',
    proxyEnabled: '启用网络代理',
    proxyUrl: '代理地址',
    captionPreset: '字幕视频压缩',
    captionCrf: '字幕视频质量 CRF',
    smallerSlower: '更小，较慢',
    balanced: '均衡，推荐',
    faster: '较快',
    fastestLarger: '最快，文件较大',
    speed: '速度',
    pitch: '音调',
    volume: '音量',
    start: '开始处理',
    waiting: '等待任务',
    stop: '停止任务',
    preview: '预览',
    emptyPreview: '处理完成后显示音视频预览',
    originalSubtitle: '识别字幕',
    translatedSubtitle: '翻译字幕',
    loadTaskSubtitles: '加载该任务字幕',
    clearSubtitleBox: '清空字幕框',
    saveAndDub: '保存并重新配音',
    saveAndCaption: '保存并生成字幕视频',
    retranslate: '用当前引擎重新翻译',
    originalPlaceholder: '识别完成后显示原文 SRT',
    translatedPlaceholder: '翻译完成后可在这里微调或粘贴 SRT',
    history: '任务历史',
    refresh: '刷新',
    backendOffline: '后端服务未连接。',
    uiLanguage: '界面语言',
  },
  en: {
    appTitle: 'Local Video Translator & Dubbing',
    appSubtitle: 'Upload a file or paste a YouTube URL, then download, transcribe, translate, dub, and render video locally.',
    ready: 'Ready',
    setupNeeded: 'Setup needed',
    settings: 'Task Settings',
    expandSettings: 'Expand settings',
    collapseSettings: 'Collapse settings',
    resetSettings: 'Clear saved settings',
    localFile: 'Local file',
    chooseMedia: 'Choose audio or video',
    youtube: 'YouTube',
    youtubeUrl: 'YouTube video URL',
    pipelineStep: 'Process until',
    sourceLanguage: 'Source language',
    targetLanguage: 'Target language',
    translationEngine: 'Translation engine',
    googleTranslate: 'Google Translate',
    openaiTranslate: 'ChatGPT / OpenAI-compatible API',
    model: 'Model',
    whisperModel: 'Whisper model',
    ttsEngine: 'Dubbing engine',
    ttsAuto: 'Auto, fallback to local after Edge fails',
    ttsLocal: 'Local SAPI offline',
    ttsEdge: 'Edge-TTS online',
    edgeVoice: 'Edge-TTS voice',
    proxyEnabled: 'Use network proxy',
    proxyUrl: 'Proxy URL',
    captionPreset: 'Caption video compression',
    captionCrf: 'Caption video quality CRF',
    smallerSlower: 'Smaller, slower',
    balanced: 'Balanced, recommended',
    faster: 'Faster',
    fastestLarger: 'Fastest, larger files',
    speed: 'Speed',
    pitch: 'Pitch',
    volume: 'Volume',
    start: 'Start',
    waiting: 'Waiting',
    stop: 'Stop task',
    preview: 'Preview',
    emptyPreview: 'Audio or video preview appears after processing',
    originalSubtitle: 'Recognized subtitles',
    translatedSubtitle: 'Translated subtitles',
    loadTaskSubtitles: 'Load task subtitles',
    clearSubtitleBox: 'Clear subtitle box',
    saveAndDub: 'Save and redub',
    saveAndCaption: 'Save and render captioned video',
    retranslate: 'Retranslate with current engine',
    originalPlaceholder: 'Original SRT appears after transcription',
    translatedPlaceholder: 'Edit or paste translated SRT here',
    history: 'Task history',
    refresh: 'Refresh',
    backendOffline: 'Backend is not reachable.',
    uiLanguage: 'Interface language',
  },
};

const optionText = {
  pipeline: {
    download: { zh: '只下载视频', en: 'Download video only' },
    subtitle: { zh: '下载/上传后识别字幕', en: 'Transcribe subtitles' },
    translate: { zh: '识别并翻译字幕', en: 'Transcribe and translate' },
    caption: { zh: '添加翻译字幕到视频', en: 'Render translated subtitles into video' },
    dub: { zh: '完整流程：翻译、配音、合成', en: 'Full workflow: translate, dub, mux' },
  },
  cont: {
    subtitle: { zh: '继续识别字幕', en: 'Continue transcription' },
    translate: { zh: '继续翻译字幕', en: 'Continue translation' },
    caption: { zh: '继续生成字幕视频', en: 'Continue captioned video' },
    dub: { zh: '继续完整配音合成', en: 'Continue full dubbing' },
  },
  languages: {
    auto: { zh: '自动检测', en: 'Auto detect' },
    'zh-CN': { zh: '简体中文', en: 'Simplified Chinese' },
    'zh-TW': { zh: '繁体中文', en: 'Traditional Chinese' },
    en: { zh: '英语', en: 'English' },
    ja: { zh: '日语', en: 'Japanese' },
    ko: { zh: '韩语', en: 'Korean' },
    es: { zh: '西班牙语', en: 'Spanish' },
    fr: { zh: '法语', en: 'French' },
    de: { zh: '德语', en: 'German' },
  },
};

const languageCodes = ['auto', 'zh-CN', 'zh-TW', 'en', 'ja', 'ko', 'es', 'fr', 'de'];
const pipelineCodes = ['download', 'subtitle', 'translate', 'caption', 'dub'];
const continueCodes = ['subtitle', 'translate', 'caption', 'dub'];
const modelOptions = ['base', 'small', 'medium', 'large-v3'];
const voiceOptions = [
  ['zh-CN-XiaoxiaoNeural', 'Xiaoxiao / Mandarin Chinese'],
  ['zh-CN-YunjianNeural', 'Yunjian / Mandarin Chinese'],
  ['en-US-JennyNeural', 'Jenny / English US'],
  ['en-US-GuyNeural', 'Guy / English US'],
  ['ja-JP-NanamiNeural', 'Nanami / Japanese'],
  ['ko-KR-SunHiNeural', 'SunHi / Korean'],
  ['es-ES-ElviraNeural', 'Elvira / Spanish'],
];

const defaultForm = {
  pipeline_step: 'dub',
  source_language: 'auto',
  target_language: 'zh-CN',
  translation_provider: 'google',
  openai_api_key: '',
  openai_base_url: 'https://api.openai.com/v1',
  openai_model: 'gpt-4o-mini',
  whisper_model: 'base',
  tts_voice: 'zh-CN-XiaoxiaoNeural',
  tts_engine: 'auto',
  tts_rate: 0,
  tts_pitch: 0,
  tts_volume: 0,
  proxy_enabled: true,
  proxy_url: 'http://127.0.0.1:7890',
  caption_preset: 'medium',
  caption_crf: 28,
};

function loadSavedForm() {
  try {
    const raw = localStorage.getItem('voiceProLocalSettings');
    return raw ? { ...defaultForm, ...JSON.parse(raw) } : defaultForm;
  } catch {
    return defaultForm;
  }
}

function loadSavedLanguage() {
  return localStorage.getItem('voiceProLocalLanguage') || 'zh';
}

function fileUrl(path) {
  return `${API_BASE}/api/files/${encodeURIComponent(path).replaceAll('%2F', '/')}`;
}

function preferredVideo(job) {
  return (
    job?.artifacts?.find((item) => item.key === 'dubbed_video')
    || job?.artifacts?.find((item) => item.key === 'subtitled_video')
    || job?.artifacts?.find((item) => item.kind === 'media')
  );
}

function mediaIcon(kind) {
  if (kind === 'video' || kind === 'media') return <FileVideo size={18} />;
  if (kind === 'audio') return <FileAudio size={18} />;
  return <Download size={18} />;
}

function App() {
  const [uiLang, setUiLang] = React.useState(loadSavedLanguage);
  const t = i18n[uiLang];
  const [sourceMode, setSourceMode] = React.useState('upload');
  const [file, setFile] = React.useState(null);
  const [youtubeUrl, setYoutubeUrl] = React.useState('');
  const [job, setJob] = React.useState(null);
  const [jobs, setJobs] = React.useState([]);
  const [health, setHealth] = React.useState(null);
  const [originalSrt, setOriginalSrt] = React.useState('');
  const [translatedSrt, setTranslatedSrt] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [settingsOpen, setSettingsOpen] = React.useState(false);
  const [form, setForm] = React.useState(loadSavedForm);

  const active = job?.status === 'queued' || job?.status === 'running';
  const video = preferredVideo(job);
  const audio = job?.artifacts?.find((item) => item.key === 'dubbed_audio' || item.key === 'source_audio');
  const canStart = sourceMode === 'upload' ? Boolean(file) : Boolean(youtubeUrl.trim());

  async function refreshHealth() {
    const res = await fetch(`${API_BASE}/api/health`);
    setHealth(await res.json());
  }

  async function refreshJobs() {
    const res = await fetch(`${API_BASE}/api/jobs`);
    setJobs(await res.json());
  }

  async function refreshJob(id = job?.id) {
    if (!id) return;
    const res = await fetch(`${API_BASE}/api/jobs/${id}`);
    if (res.ok) setJob(await res.json());
  }

  async function loadSubtitles(id = job?.id) {
    if (!id) return;
    const original = await fetch(`${API_BASE}/api/jobs/${id}/subtitles/original`);
    setOriginalSrt(original.ok ? (await original.json()).content : '');
    const translated = await fetch(`${API_BASE}/api/jobs/${id}/subtitles/translated`);
    setTranslatedSrt(translated.ok ? (await translated.json()).content : '');
  }

  React.useEffect(() => {
    refreshHealth().catch(() => setHealth({ ok: false, errors: [t.backendOffline] }));
    refreshJobs().catch(() => {});
  }, []);

  React.useEffect(() => {
    localStorage.setItem('voiceProLocalSettings', JSON.stringify(form));
  }, [form]);

  React.useEffect(() => {
    localStorage.setItem('voiceProLocalLanguage', uiLang);
  }, [uiLang]);

  React.useEffect(() => {
    if (!job?.id || !active) return undefined;
    const timer = setInterval(() => refreshJob(job.id), 1600);
    return () => clearInterval(timer);
  }, [job?.id, active]);

  React.useEffect(() => {
    if (job?.status === 'completed' || job?.status === 'failed' || job?.status === 'cancelled') {
      refreshJobs().catch(() => {});
    }
  }, [job?.id, job?.status]);

  async function startJob(event) {
    event.preventDefault();
    if (!canStart) return;
    const payload = new FormData();
    if (sourceMode === 'upload') payload.append('file', file);
    if (sourceMode === 'youtube') payload.append('youtube_url', youtubeUrl.trim());
    Object.entries(form).forEach(([key, value]) => payload.append(key, value));
    const res = await fetch(`${API_BASE}/api/jobs`, { method: 'POST', body: payload });
    setJob(await res.json());
    setOriginalSrt('');
    setTranslatedSrt('');
  }

  async function saveAndRerun() {
    if (!job?.id) return;
    setSaving(true);
    try {
      await fetch(`${API_BASE}/api/jobs/${job.id}/subtitles/translated`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: translatedSrt }),
      });
      const res = await fetch(`${API_BASE}/api/jobs/${job.id}/rerun-dubbing`, { method: 'POST' });
      setJob(await res.json());
    } finally {
      setSaving(false);
    }
  }

  async function continueJob(step, options = {}) {
    if (!job?.id) return;
    const res = await fetch(`${API_BASE}/api/jobs/${job.id}/continue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pipeline_step: step,
        force_retranslate: Boolean(options.force_retranslate),
        translation_provider: form.translation_provider,
        openai_api_key: form.openai_api_key,
        openai_base_url: form.openai_base_url,
        openai_model: form.openai_model,
      }),
    });
    setJob(await res.json());
  }

  async function saveAndCaption() {
    if (!job?.id) return;
    setSaving(true);
    try {
      await fetch(`${API_BASE}/api/jobs/${job.id}/subtitles/translated`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: translatedSrt }),
      });
      const res = await fetch(`${API_BASE}/api/jobs/${job.id}/render-caption`, { method: 'POST' });
      setJob(await res.json());
    } finally {
      setSaving(false);
    }
  }

  async function cancelJob() {
    if (!job?.id) return;
    const res = await fetch(`${API_BASE}/api/jobs/${job.id}/cancel`, { method: 'POST' });
    if (res.ok) setJob(await res.json());
  }

  function resetSettings() {
    localStorage.removeItem('voiceProLocalSettings');
    setForm(defaultForm);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>{t.appTitle}</h1>
          <p>{t.appSubtitle}</p>
        </div>
        <div className="topbar-actions">
          <label className="language-switch">
            {t.uiLanguage}
            <select value={uiLang} onChange={(event) => setUiLang(event.target.value)}>
              <option value="zh">简体中文</option>
              <option value="en">English</option>
            </select>
          </label>
          <div className={health?.ok ? 'health ok' : 'health bad'}>
            {health?.ok ? t.ready : t.setupNeeded}
          </div>
        </div>
      </header>

      {health && !health.ok && (
        <section className="notice">
          {health.errors?.map((item) => <span key={item}>{item}</span>)}
        </section>
      )}

      <section className="workspace-grid">
        <form className="panel controls" onSubmit={startJob}>
          <div className="form-header">
            <strong>{t.settings}</strong>
            <div className="form-header-actions">
              <button type="button" onClick={() => setSettingsOpen(!settingsOpen)}>
                {settingsOpen ? t.collapseSettings : t.expandSettings}
              </button>
              <button type="button" onClick={resetSettings}>{t.resetSettings}</button>
            </div>
          </div>

          <div className="segmented">
            <button type="button" className={sourceMode === 'upload' ? 'active' : ''} onClick={() => setSourceMode('upload')}>
              <UploadCloud size={16} />
              {t.localFile}
            </button>
            <button type="button" className={sourceMode === 'youtube' ? 'active' : ''} onClick={() => setSourceMode('youtube')}>
              <Link size={16} />
              {t.youtube}
            </button>
          </div>

          {sourceMode === 'upload' ? (
            <label className="upload-zone">
              <UploadCloud size={28} />
              <input type="file" accept="audio/*,video/*,.mkv,.webm,.mp4,.mov,.wav,.mp3,.flac" onChange={(event) => setFile(event.target.files?.[0] || null)} />
              <strong>{file ? file.name : t.chooseMedia}</strong>
            </label>
          ) : (
            <label>
              {t.youtubeUrl}
              <input type="url" value={youtubeUrl} onChange={(event) => setYoutubeUrl(event.target.value)} placeholder="https://www.youtube.com/watch?v=..." />
            </label>
          )}

          <label>
            {t.pipelineStep}
            <select value={form.pipeline_step} onChange={(event) => setForm({ ...form, pipeline_step: event.target.value })}>
              {pipelineCodes.map((value) => <option key={value} value={value}>{optionText.pipeline[value][uiLang]}</option>)}
            </select>
          </label>

          {settingsOpen && (
            <div className="settings-body">
              <div className="field-row">
                <label>
                  {t.sourceLanguage}
                  <select value={form.source_language} onChange={(event) => setForm({ ...form, source_language: event.target.value })}>
                    {languageCodes.map((value) => <option key={value} value={value}>{optionText.languages[value][uiLang]}</option>)}
                  </select>
                </label>
                <label>
                  {t.targetLanguage}
                  <select value={form.target_language} onChange={(event) => setForm({ ...form, target_language: event.target.value })}>
                    {languageCodes.filter((value) => value !== 'auto').map((value) => <option key={value} value={value}>{optionText.languages[value][uiLang]}</option>)}
                  </select>
                </label>
              </div>

              <label>
                {t.translationEngine}
                <select value={form.translation_provider} onChange={(event) => setForm({ ...form, translation_provider: event.target.value })}>
                  <option value="google">{t.googleTranslate}</option>
                  <option value="openai">{t.openaiTranslate}</option>
                </select>
              </label>

              {form.translation_provider === 'openai' && (
                <div className="api-box">
                  <label>API Key<input type="password" value={form.openai_api_key} onChange={(event) => setForm({ ...form, openai_api_key: event.target.value })} placeholder="sk-..." /></label>
                  <label>Base URL<input type="text" value={form.openai_base_url} onChange={(event) => setForm({ ...form, openai_base_url: event.target.value })} placeholder="https://api.openai.com/v1" /></label>
                  <label>{t.model}<input type="text" value={form.openai_model} onChange={(event) => setForm({ ...form, openai_model: event.target.value })} placeholder="gpt-4o-mini" /></label>
                </div>
              )}

              <label>
                {t.whisperModel}
                <select value={form.whisper_model} onChange={(event) => setForm({ ...form, whisper_model: event.target.value })}>
                  {modelOptions.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>

              <label>
                {t.ttsEngine}
                <select value={form.tts_engine} onChange={(event) => setForm({ ...form, tts_engine: event.target.value })}>
                  <option value="auto">{t.ttsAuto}</option>
                  <option value="local">{t.ttsLocal}</option>
                  <option value="edge">{t.ttsEdge}</option>
                </select>
              </label>

              <label>
                {t.edgeVoice}
                <select value={form.tts_voice} onChange={(event) => setForm({ ...form, tts_voice: event.target.value })}>
                  {voiceOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </label>

              <label className="check-row">
                <input type="checkbox" checked={form.proxy_enabled} onChange={(event) => setForm({ ...form, proxy_enabled: event.target.checked })} />
                {t.proxyEnabled}
              </label>

              <label>
                {t.proxyUrl}
                <input type="text" value={form.proxy_url} disabled={!form.proxy_enabled} onChange={(event) => setForm({ ...form, proxy_url: event.target.value })} placeholder="http://127.0.0.1:7890" />
              </label>

              <div className="field-row">
                <label>
                  {t.captionPreset}
                  <select value={form.caption_preset} onChange={(event) => setForm({ ...form, caption_preset: event.target.value })}>
                    <option value="slow">{t.smallerSlower}</option>
                    <option value="medium">{t.balanced}</option>
                    <option value="fast">{t.faster}</option>
                    <option value="ultrafast">{t.fastestLarger}</option>
                  </select>
                </label>
                <label>{t.captionCrf}<input type="number" min="18" max="35" value={form.caption_crf} onChange={(event) => setForm({ ...form, caption_crf: Number(event.target.value) })} /></label>
              </div>

              <div className="field-row compact">
                <label>{t.speed}<input type="number" min="-50" max="50" value={form.tts_rate} onChange={(event) => setForm({ ...form, tts_rate: Number(event.target.value) })} /></label>
                <label>{t.pitch}<input type="number" min="-100" max="100" value={form.tts_pitch} onChange={(event) => setForm({ ...form, tts_pitch: Number(event.target.value) })} /></label>
                <label>{t.volume}<input type="number" min="-50" max="50" value={form.tts_volume} onChange={(event) => setForm({ ...form, tts_volume: Number(event.target.value) })} /></label>
              </div>
            </div>
          )}

          <button className="primary-button" disabled={!canStart || active}>
            {active ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
            {t.start}
          </button>
        </form>

        <section className="panel progress-panel">
          <div className="panel-title"><Mic2 size={18} /><h2>{job ? job.stage : t.waiting}</h2></div>
          <div className="progress-track"><span style={{ width: `${job?.progress || 0}%` }} /></div>
          <div className="status-line"><span>{job?.status || 'idle'}</span><span>{job?.progress || 0}%</span></div>
          {active && <button className="stop-button" type="button" onClick={cancelJob}><Square size={16} />{t.stop}</button>}
          {job?.error && <p className="error-text">{job.error}</p>}
          {job && !active && (
            <div className="continue-actions">
              {continueCodes.map((step) => (
                <button key={step} type="button" onClick={() => continueJob(step, { force_retranslate: step === 'translate' })}>
                  {optionText.cont[step][uiLang]}
                </button>
              ))}
            </div>
          )}
          <div className="log-box">{(job?.logs || []).map((item, index) => <p key={`${index}-${item}`}>{item}</p>)}</div>
        </section>

        <section className="panel preview-panel">
          <div className="panel-title"><FileVideo size={18} /><h2>{t.preview}</h2></div>
          {video ? <video src={fileUrl(video.path)} controls /> : audio ? <audio src={fileUrl(audio.path)} controls /> : <div className="empty-preview">{t.emptyPreview}</div>}
          <div className="artifact-list">
            {(job?.artifacts || []).map((item) => (
              <a key={item.key} href={fileUrl(item.path)} target="_blank" rel="noreferrer">{mediaIcon(item.kind)}<span>{item.label}</span></a>
            ))}
          </div>
        </section>
      </section>

      <section className="subtitle-grid">
        <div className="panel editor-panel">
          <div className="editor-title"><h2>{t.originalSubtitle}</h2><button onClick={() => loadSubtitles()} disabled={!job?.id || active}><Download size={16} />{t.loadTaskSubtitles}</button></div>
          <textarea value={originalSrt} readOnly placeholder={t.originalPlaceholder} />
        </div>
        <div className="panel editor-panel">
          <div className="editor-title">
            <h2>{t.translatedSubtitle}</h2>
            <button onClick={() => setTranslatedSrt('')} disabled={active}>{t.clearSubtitleBox}</button>
            <button onClick={saveAndRerun} disabled={!translatedSrt || active || saving}>{saving || active ? <Loader2 className="spin" size={16} /> : <Save size={16} />}{t.saveAndDub}</button>
            <button onClick={saveAndCaption} disabled={!translatedSrt || active || saving}>{saving || active ? <Loader2 className="spin" size={16} /> : <Save size={16} />}{t.saveAndCaption}</button>
            <button onClick={() => continueJob('translate', { force_retranslate: true })} disabled={!originalSrt || active || saving}><RefreshCcw size={16} />{t.retranslate}</button>
          </div>
          <textarea value={translatedSrt} onChange={(event) => setTranslatedSrt(event.target.value)} placeholder={t.translatedPlaceholder} />
        </div>
      </section>

      <section className="history">
        <div className="history-title"><h2>{t.history}</h2><button onClick={() => refreshJobs()}><RefreshCcw size={16} />{t.refresh}</button></div>
        <div className="history-list">
          {jobs.map((item) => (
            <button key={item.id} className={job?.id === item.id ? 'selected' : ''} onClick={() => { setJob(item); setOriginalSrt(''); setTranslatedSrt(''); }}>
              <span>{item.input_name}</span>
              <small>{item.status} · {item.progress}%</small>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
