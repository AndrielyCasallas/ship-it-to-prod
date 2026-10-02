'use client'

import { useEffect, useState } from 'react'
import {
  ArrowUpRight,
  AtSign,
  CalendarDays,
  Code2,
  Check,
  MessageCircle,
  Menu,
  Radio,
  Send,
  Sparkles,
  Users,
  X,
  Zap,
} from 'lucide-react'

type ApiEvent = { id: number; title: string; description: string; event_date: string; created_by: number }
type Attendee = { display_name: string; registered_at: string }
type Health = { status: string; database: string }
type Project = { id: number; title: string; description: string; manager: string; repository_url?: string; landing_page_url?: string; status: string; created_at: string }
type CoreMember = { id: number; name: string; role: string; instagram?: string; linkedin?: string; github?: string }
type ProjectForm = { name: string; manager: string; contact_phone: string; contact_email: string; description: string }
type SpeakerForm = { name: string; company: string; job_title: string; email: string; phone: string }

const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const API_URL = configuredApiUrl === '/api'
  ? ''
  : configuredApiUrl.replace(/\/$/, '')
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? ''
const communityLinks = [
  { label: 'Comunidad de WhatsApp', url: process.env.NEXT_PUBLIC_WHATSAPP_URL ?? '', icon: MessageCircle },
  { label: 'Instagram', url: process.env.NEXT_PUBLIC_INSTAGRAM_URL ?? '', icon: AtSign },
  { label: 'Meetup', url: process.env.NEXT_PUBLIC_MEETUP_URL ?? '', icon: CalendarDays },
  { label: 'Telegram · consultas', url: process.env.NEXT_PUBLIC_TELEGRAM_URL ?? '', icon: Send },
  { label: 'LinkedIn', url: process.env.NEXT_PUBLIC_LINKEDIN_URL ?? '', icon: Code2 },
]

const apiHeaders = {
  'X-API-Key': API_KEY,
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: 'no-store', headers: apiHeaders })
  if (!response.ok) throw new Error(`API ${response.status}`)
  return response.json()
}

async function postJson<T>(path: string, body: T) {
  const response = await fetch(`${API_URL}${path}`, { method: 'POST', headers: { ...apiHeaders, 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!response.ok) throw new Error(`API ${response.status}`)
  return response.json().catch(() => null)
}

type DateParts = { year: number; month: number; day: number }

function parseDateParts(value: string): DateParts | null {
  const date = value.trim()
  const isoMatch = date.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (isoMatch) return { year: Number(isoMatch[1]), month: Number(isoMatch[2]), day: Number(isoMatch[3]) }
  return null
}

function formatDate(date: string) {
  const parts = parseDateParts(date)
  if (!parts) return 'Fecha no disponible'
  const months = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
  return `${String(parts.day).padStart(2, '0')} ${months[parts.month - 1] ?? ''} ${parts.year}`
}

function AppMark() {
  return <div className="app-mark" aria-label="AWS Students Builder Group"><span>AWS</span><i /></div>
}

function Countdown({ date }: { date: string }) {
  const [now, setNow] = useState<number | null>(null)

  useEffect(() => {
    const updateNow = () => setNow(Date.now())
    updateNow()
    const timer = window.setInterval(updateNow, 1000)
    return () => window.clearInterval(timer)
  }, [])

  // Keep the server render and the first client render identical. The live clock
  // starts only after hydration, so Date.now() can never change the HTML React hydrates.
  const parts = parseDateParts(date)
  const eventTime = parts ? new Date(parts.year, parts.month - 1, parts.day, 18).getTime() : Number.NaN
  const hasValidDate = Number.isFinite(eventTime)
  const isReady = now !== null && hasValidDate
  const diff = isReady ? Math.max(0, eventTime - now) : 0
  const days = Math.floor(diff / 86400000)
  const hours = Math.floor((diff % 86400000) / 3600000)
  const mins = Math.floor((diff % 3600000) / 60000)
  const secs = Math.floor((diff % 60000) / 1000)
  const countdownLabel = isReady ? `Faltan ${days} días para el evento` : 'Fecha del evento no disponible'

  if (!hasValidDate) return <div className="countdown" aria-label={countdownLabel}><b>Fecha no disponible</b></div>

  return <div className="countdown" aria-label={countdownLabel}><div><b>{String(days).padStart(2, '0')}</b><small>DÍAS</small></div><span>:</span><div><b>{String(hours).padStart(2, '0')}</b><small>HRS</small></div><span>:</span><div><b>{String(mins).padStart(2, '0')}</b><small>MIN</small></div><span>:</span><div><b>{String(secs).padStart(2, '0')}</b><small>SEC</small></div></div>
}

function SectionLabel({ children, number }: { children: React.ReactNode; number: string }) { return <div className="section-label"><span>{number}</span><span>{children}</span></div> }

function CommunityForm({ kind, title, description }: { kind: 'project' | 'speaker'; title: string; description: string }) {
  const isProject = kind === 'project'
  const [values, setValues] = useState<ProjectForm | SpeakerForm>(isProject ? { name: '', manager: '', contact_phone: '', contact_email: '', description: '' } : { name: '', company: '', job_title: '', email: '', phone: '' })
  const [state, setState] = useState<'idle' | 'sending' | 'success' | 'error'>('idle')
  const update = (key: string, value: string) => setValues((current) => ({ ...current, [key]: value }))
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!values.name.trim() || (isProject && (!(values as ProjectForm).manager.trim() || !(values as ProjectForm).description.trim()))) return
    setState('sending')
    try { await postJson(isProject ? '/api/project-proposals' : '/api/speakers', values); setValues(isProject ? { name: '', manager: '', contact_phone: '', contact_email: '', description: '' } : { name: '', company: '', job_title: '', email: '', phone: '' }); setState('success') } catch { setState('error') }
  }
  return <article className="form-card"><div><span className="project-tag">{isProject ? 'COLABORA CON EL GRUPO' : 'COMPARTE TU EXPERIENCIA'}</span><h3>{title}</h3><p>{description}</p></div><form onSubmit={submit}><label>Nombre Completo<input required value={values.name} onChange={(event) => update('name', event.target.value)} /></label>{isProject ? <><label>Nombre del proyecto<input required value={(values as ProjectForm).manager} onChange={(event) => update('manager', event.target.value)} /></label><div className="form-row"><label>Teléfono<input value={(values as ProjectForm).contact_phone} onChange={(event) => update('contact_phone', event.target.value)} /></label><label>Email<input type="email" value={(values as ProjectForm).contact_email} onChange={(event) => update('contact_email', event.target.value)} /></label></div><label>Descripción<textarea required rows={4} value={(values as ProjectForm).description} onChange={(event) => update('description', event.target.value)} /></label></> : <><div className="form-row"><label>Empresa<input value={(values as SpeakerForm).company} onChange={(event) => update('company', event.target.value)} /></label><label>Cargo<input value={(values as SpeakerForm).job_title} onChange={(event) => update('job_title', event.target.value)} /></label></div><div className="form-row"><label>Email<input type="email" value={(values as SpeakerForm).email} onChange={(event) => update('email', event.target.value)} /></label><label>Teléfono<input value={(values as SpeakerForm).phone} onChange={(event) => update('phone', event.target.value)} /></label></div></>}<button className="button-primary" disabled={state === 'sending'}>{state === 'sending' ? 'Enviando...' : isProject ? 'Proponer proyecto' : 'Quiero ser speaker'} <ArrowUpRight size={16} /></button>{state === 'success' && <p className="form-message success">Enviado correctamente. Gracias por aportar a la comunidad.</p>}{state === 'error' && <p className="form-message error">No pudimos enviar la información. Intenta nuevamente.</p>}</form></article>
}

export default function Page() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [events, setEvents] = useState<ApiEvent[]>([])
  const [attendees, setAttendees] = useState<Attendee[]>([])
  const [projectsData, setProjectsData] = useState<Project[]>([])
  const [teamData, setTeamData] = useState<CoreMember[]>([])
  const [completedCount, setCompletedCount] = useState(0)
  const [health, setHealth] = useState<Health | null>(null)
  const [loading, setLoading] = useState(true)
  const [apiError, setApiError] = useState(false)

  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true)
      try {
        const [nextEvents, nextAttendees, nextHealth, nextProjects, nextTeam, completed] = await Promise.all([
          getJson<ApiEvent[]>('/api/events/upcoming'),
          getJson<Attendee[]>('/api/attendees'),
          getJson<Health>('/health'),
          getJson<Project[]>('/api/projects/ongoing'),
          getJson<CoreMember[]>('/api/core-team'),
          getJson<{ count: number }>('/api/events/completed/count'),
        ])
        setEvents(nextEvents)
        setAttendees(nextAttendees)
        setHealth(nextHealth)
        setProjectsData(nextProjects)
        setTeamData(nextTeam)
        setCompletedCount(completed.count)
        setApiError(false)
      } catch { setApiError(true) } finally { setLoading(false) }
    }
    const refreshAttendees = async () => {
      try {
        setAttendees(await getJson<Attendee[]>('/api/attendees'))
        setApiError(false)
      } catch {
        setApiError(true)
      }
    }
    loadInitialData()
    const refresh = window.setInterval(refreshAttendees, 10000)
    return () => window.clearInterval(refresh)
  }, [])

  useEffect(() => {
    const move = (event: MouseEvent) => { document.documentElement.style.setProperty('--mouse-x', `${event.clientX}px`); document.documentElement.style.setProperty('--mouse-y', `${event.clientY}px`) }
    window.addEventListener('pointermove', move); return () => window.removeEventListener('pointermove', move)
  }, [])

  const nextEvent = events[0] ?? null
  const nextEventDate = nextEvent ? parseDateParts(nextEvent.event_date) : null

  return (
    <main className="site-shell">
      <div className="ambient-grid" aria-hidden="true" /><div className="cursor-glow" aria-hidden="true" />
      <nav className="nav container"><a className="brand" href="#top"><AppMark /><span>STUDENTS<br /><strong>BUILDER GROUP</strong></span></a><div className={`nav-links ${menuOpen ? 'is-open' : ''}`}><a href="#about" onClick={() => setMenuOpen(false)}>Nosotros</a><a href="#projects" onClick={() => setMenuOpen(false)}>Proyectos</a><a href="#calendar" onClick={() => setMenuOpen(false)}>Calendario</a><a href="#team" onClick={() => setMenuOpen(false)}>El team</a></div><a className="nav-cta" href="#join">Únete al grupo <ArrowUpRight size={16} /></a><button className="menu-toggle" aria-label="Abrir menú" onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X /> : <Menu />}</button></nav>

      <section className="hero container" id="top"><div className="hero-copy"><div className="eyebrow"><span className="pulse-dot" /> AWS STUDENT BUILDER GROUP · LA SALLE 2026</div><h1>Construimos<br /><em>el futuro</em><br />juntos<span className="orange-dot">.</span></h1><p className="hero-intro">Una comunidad de builders, estudiantes y soñadores creando soluciones reales con tecnología cloud.</p><div className="hero-actions"><a className="button-primary" href="#join">Conoce la comunidad <ArrowUpRight size={18} /></a><a className="text-link" href="#about">Explora el movimiento <span>↓</span></a></div></div><div className="hero-orbit" aria-hidden="true"><div className="orbit-ring ring-one" /><div className="orbit-ring ring-two" /><div className="orbit-core"><span className="core-label">AWS<br />STUDENTS</span><Zap size={30} /></div><span className="orbit-node node-one">BUILD<br />TOGETHER</span><span className="orbit-node node-two">LEARN<br />IN PUBLIC</span><span className="orbit-node node-three">SHIP<br />IMPACT</span></div><div className="hero-foot"><span className="line" /></div></section>

      <section className="stats-strip"><div className="container stat-grid"><div><b>{loading ? '—' : attendees.length}</b><span>asistentes registrados</span></div><div><b>{loading ? '—' : completedCount}</b><span>eventos realizados</span></div><div><b>{loading ? '—' : projectsData.length}</b><span>proyectos en curso</span></div><div className="status"><span className={`status-dot ${health && !apiError ? 'online' : ''}`} /> <span>{loading ? 'Sincronizando API...' : apiError ? 'No hay Conexión' : 'Datos en vivo'}</span></div></div></section>

      <section className="about section container" id="about"><SectionLabel number="01">LA COMUNIDAD</SectionLabel><div className="about-layout"><div><h2>No venimos a<br /><span>observar.</span></h2><p className="large-copy">Venimos a construir. AWS Students Builder Group es el punto de encuentro para quienes quieren transformar ideas en impacto usando cloud.</p></div><div className="mission-cards"><article><Sparkles size={20} /><h3>Misión</h3><p>Democratizar el acceso al conocimiento cloud y acompañar a cada builder en su camino.</p></article><article><Radio size={20} /><h3>Visión</h3><p>Una generación de creadores latinoamericanos que resuelve lo imposible juntos.</p></article></div></div></section>

      <section className="event-section section" id="events"><div className="container"><SectionLabel number="02">PRÓXIMO ENCUENTRO</SectionLabel>{nextEvent ? <div className="event-layout"><div className="event-date"><span className="event-month">{nextEventDate ? String(nextEventDate.month).padStart(2, '0') : '--'}</span><strong>{nextEventDate ? String(nextEventDate.day).padStart(2, '0') : '--'}</strong><span className="event-year">{nextEventDate?.year ?? '----'}</span></div><div className="event-detail"><div className="event-tag"><span className="pulse-dot" /> EVENTO DEL API</div><h2>{nextEvent.title}</h2><p>{nextEvent.description}</p><div className="event-meta"><span><CalendarDays size={17} /> {formatDate(nextEvent.event_date)}</span></div></div><div className="countdown-wrap"><span>COMIENZA EN</span><Countdown date={nextEvent.event_date} /></div></div> : <p className="empty-state">{loading ? 'Cargando el próximo evento...' : apiError ? 'No se pudo consultar el próximo evento.' : 'No hay próximos eventos registrados.'}</p>}</div></section>

      <section className="projects section container" id="projects"><SectionLabel number="03">PROYECTOS EN CURSO</SectionLabel><div className="section-heading"><h2>Ideas en <span>movimiento.</span></h2></div><div className="project-list">{projectsData.length ? projectsData.map((project, index) => <article className={`project-card ${['orange', 'violet', 'cyan'][index % 3]}`} key={project.id}><span className="project-number">{String(project.id).padStart(2, '0')}</span><div><span className="project-tag">{project.status}</span><h3>{project.title}</h3><p>{project.description}</p><small>{project.manager}</small></div><div className="project-links">{project.repository_url && <a href={project.repository_url} target="_blank" rel="noreferrer">Repositorio <ArrowUpRight size={15} /></a>}{project.landing_page_url && <a href={project.landing_page_url} target="_blank" rel="noreferrer">Landing <ArrowUpRight size={15} /></a>}</div></article>) : <p className="empty-state">{loading ? 'Cargando proyectos...' : apiError ? 'No se pudieron consultar los proyectos.' : 'No hay proyectos en curso registrados.'}</p>}</div></section>

      <section className="live-data section container" id="live-data"><SectionLabel number="03B">DATOS EN TIEMPO REAL</SectionLabel><div className="live-grid"><div className="live-card"><div className="live-card-head"><h3>Próximos eventos</h3><span>{loading ? 'Cargando...' : `${events.length} publicados`}</span></div>{events.length ? events.slice(0, 3).map((event) => <div className="live-row" key={event.id}><CalendarDays size={16} /><div><b>{event.title}</b><small>{formatDate(event.event_date)} · {event.description}</small></div></div>) : <p className="empty-state">{apiError ? 'La API no está disponible. Los eventos aparecerán aquí al conectar el backend.' : 'Aún no hay eventos publicados.'}</p>}</div><div className="live-card"><div className="live-card-head"><h3>Builders registrados</h3><span>{loading ? 'Cargando...' : `${attendees.length} asistentes`}</span></div>{attendees.length ? attendees.slice(0, 4).map((attendee) => <div className="live-row" key={`${attendee.display_name}-${attendee.registered_at}`}><Users size={16} /><div><b>{attendee.display_name}</b><small>Registrado el {formatDate(attendee.registered_at.slice(0, 10))}</small></div></div>) : <p className="empty-state">{apiError ? 'Conecta la API para mostrar la lista de asistentes.' : 'Todavía no hay asistentes registrados.'}</p>}</div></div></section>

      <section className="calendar-section section" id="calendar"><div className="container"><SectionLabel number="04">PRÓXIMOS EVENTOS</SectionLabel><div className="section-heading"><h2>Poximos <span>eventos.</span></h2></div><div className="calendar-grid">{events.length ? events.map((event) => <div className="calendar-item" key={event.id}><span>{formatDate(event.event_date)}</span><b>{event.title}</b><small>{event.description}</small></div>) : <p className="empty-state">{loading ? 'Cargando agenda...' : apiError ? 'No se pudo consultar la agenda.' : 'No hay eventos próximos registrados.'}</p>}</div></div></section>

      <section className="people section container" id="team"><SectionLabel number="05">QUIENES LO HACEN POSIBLE</SectionLabel><div className="section-heading team-heading"><h2>El team detrás<br />del <span>movimiento.</span></h2></div><div className="team-grid">{teamData.length ? teamData.map((person, index) => <article className="person" key={person.id}><div className={`avatar ${['orange', 'violet', 'cyan', 'pink'][index % 4]}`}>{person.name.split(' ').map((part) => part[0]).join('').slice(0, 2)}</div><h3>{person.name}</h3><span>{person.role}</span><div className="person-links">{person.instagram && <a href={person.instagram} target="_blank" rel="noreferrer"><AtSign size={15} /> Instagram</a>}{person.linkedin && <a href={person.linkedin} target="_blank" rel="noreferrer"><AtSign size={15} /> LinkedIn</a>}{person.github && <a href={person.github} target="_blank" rel="noreferrer"><Code2 size={15} /> GitHub</a>}</div></article>) : <p className="empty-state">{loading ? 'Cargando core team...' : apiError ? 'No se pudo consultar el core team.' : 'No hay miembros del core team registrados.'}</p>}</div></section>

      <section className="contribute section container" id="contribute"><SectionLabel number="06">PARTICIPA</SectionLabel><div className="section-heading"><h2>Tu idea puede<br /><span>ser la próxima.</span></h2><p>Propón un proyecto o comparte tu conocimiento con la comunidad.</p></div><div className="forms-grid"><CommunityForm kind="project" title="Propón un proyecto" description="Cuéntanos qué quieres construir y encuentra builders para hacerlo realidad." /><CommunityForm kind="speaker" title="Regístrate como speaker" description="Comparte tu experiencia y ayuda a otros estudiantes a dar el siguiente paso." /></div></section>

      <section className="join-section" id="join"><div className="container join-inner"><div className="join-graphic" aria-hidden="true"><div className="join-cross">+</div><div className="join-orbit" /></div><div><span className="eyebrow">PARTICIPA EN LA COMUNIDAD</span><h2>¿Listo para<br /><em>construir?</em></h2><p>Encuentra la comunidad y elige el canal que prefieras.</p><div className="community-links">{communityLinks.map(({ label, url, icon: Icon }) => url ? <a className="community-link" href={url} target="_blank" rel="noreferrer" key={label}><Icon size={18} /> <span>{label}</span><ArrowUpRight size={15} /></a> : <span className="community-link is-disabled" key={label} aria-disabled="true"><Icon size={18} /> <span>{label}</span><small>Configura el enlace</small></span>)}</div></div></div></section>

      <footer className="footer container"><a className="brand" href="#top"><AppMark /><span>STUDENTS<br /><strong>BUILDER GROUP</strong></span></a></footer>

      <aside className="api-panel" aria-live="polite"><span className={`status-dot ${!apiError && !loading ? 'online' : ''}`} /> {loading ? 'Consultando asistentes...' : apiError ? 'API de asistentes no disponible' : `${attendees.length} asistentes sincronizados`} {!loading && !apiError && <Check size={13} />}</aside>
    </main>
  )
}
